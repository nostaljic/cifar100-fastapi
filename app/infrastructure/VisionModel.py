from abc import ABC, abstractmethod
import logging


class IVisionModel(ABC):
    @abstractmethod
    def preprocess_image(self, image_data: bytes):
        pass

    @abstractmethod
    def run_inference(self, image_data: bytes):
        pass

    @abstractmethod
    def get_top_k_predictions(self, output, ks) -> dict:
        pass


import json
import tensorflow as tf
import numpy as np
from typing import Any
from PIL import Image
import io
from app.infrastructure.Environment import get_environment_variables, get_root_dir

with open(
    f"{get_root_dir()}{get_environment_variables().CIFAR100_LABEL_PATH}", "r"
) as file:
    CIFAR100_CLASSES = json.load(file)


class TFLiteVisionModel(IVisionModel):
    def __init__(self):
        self.env = get_environment_variables()
        self.root_dir = get_root_dir()
        self.interpreter = tf.lite.Interpreter(
            model_path=f"{self.root_dir}{self.env.TFLITE_MODEL_PATH}"
        )
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        image = image.resize((128, 128))
        image_array = np.array(image).astype(np.float32) / 255.0
        image_array = np.expand_dims(image_array, axis=0)
        return image_array

    def run_inference(self, image_data: bytes) -> np.ndarray:
        input_data = self.preprocess_image(image_data)
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]["index"])
        return output_data

    def get_top_k_predictions(self, output: np.ndarray, k: int = 5) -> dict:
        top_k_indices = np.argsort(-output, axis=1)[:, :k]

        top_k_labels = [
            [CIFAR100_CLASSES[idx] for idx in indices] for indices in top_k_indices
        ][0]
        top_k_possibility = [
            [float(output[0][idx]) for idx in indices] for indices in top_k_indices
        ][0]

        logging.info("[LOG] Inference Result :", top_k_labels)
        return dict(zip(top_k_labels, top_k_possibility))


import cv2
import numpy as np
import onnxruntime as ort
from abc import ABC, abstractmethod


# 11/13일자 모델 : ['batch_size', 3, 128, 128] (NCHW)
class ONNXVisionModel(IVisionModel):
    def __init__(self):
        self.env = get_environment_variables()
        self.root_dir = get_root_dir()
        self.session = ort.InferenceSession(
            f"{self.root_dir}{self.env.ONNX_MODEL_PATH}"
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape

    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        image = cv2.resize(image, (self.input_shape[3], self.input_shape[2]))
        image = image.astype(np.float32) / 255.0
        # 이미지 형식 조정 : HWC (높이, 너비, 채널) -> CHW (채널, 높이, 너비)
        image = np.transpose(image, (2, 0, 1))
        # 배치 차원 추가: (3, 128, 128) -> (1, 3, 128, 128)
        image = np.expand_dims(image, axis=0)
        return image

    def run_inference(self, image_data: bytes) -> np.ndarray:
        # 이미지를 전처리하고 추론 실행
        preprocessed_image = self.preprocess_image(image_data)
        outputs = self.session.run(
            [self.output_name], {self.input_name: preprocessed_image}
        )
        return outputs[0]

    def get_top_k_predictions(self, output, k: int = 5) -> dict:
        # 출력값을 평탄화하고 상위 k개의 예측 결과를 가져옴
        output = output.flatten()
        top_k_indices = output.argsort()[-k:][::-1]
        top_k_labels = [CIFAR100_CLASSES[i] for i in top_k_indices]
        top_k_scores = [float(o) for o in output[top_k_indices]]
        return dict(zip(top_k_labels, top_k_scores))


"""
# tflite -> onnx 변환 모델 : [1, 128, 128, 3] (1HWC) *N=1이다.
class ONNXVisionModel(IVisionModel):
    def __init__(self):
        self.env = get_environment_variables()
        self.root_dir = get_root_dir()
        self.session = ort.InferenceSession(f"{self.root_dir}{self.env.ONNX_MODEL_PATH}")
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape

    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        image = cv2.resize(image, (self.input_shape[2], self.input_shape[1]))
        image = image.astype(np.float32) / 255.0
        image = np.expand_dims(image, axis=0)
        return image

    def run_inference(self, image_data: bytes) -> np.ndarray:
        preprocessed_image = self.preprocess_image(image_data)
        outputs = self.session.run(
            [self.output_name], {self.input_name: preprocessed_image}
        )
        return outputs[0]

    def get_top_k_predictions(self, output, k: int = 5) -> dict:
        output = output.flatten()
        top_k_indices = output.argsort()[-k:][::-1]
        top_k_labels = [CIFAR100_CLASSES[i] for i in top_k_indices]
        top_k_scores = [float(o) for o in output[top_k_indices]]
        return dict(zip(top_k_labels, top_k_scores))
"""
