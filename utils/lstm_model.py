import unidecode
import functools
import numpy as np
import tensorflow as tf
from tensorflow.keras import backend as K
from tensorflow.keras.models import load_model

alphabet = "abcdefghijklmnopqrstuvwxyz"


def is_alpha(name):
    """
    name이 알파벳으로만 이루어진 문자열인지 판별
    """
    for c in name:
        if c.lower() not in alphabet:
            return False
    return True


def normalize(name):
    """
    유니코드 문자(ex. 한자 or À 이런 애들)를 ascii 알파벳으로 바꾸고
    알파벳만 남김
    """
    result = ""
    for c in unidecode.unidecode(name):
        if c.lower() in alphabet:
            result += c
    return result


def scale(x):
    """
    first name이 kr인지 계산할 때 쓰이는 scale함수
    """
    if x < 1 / 3:
        return x * 1.5
    else:
        return 0.75 * x + 0.25


def name_one_hot(name, max_seq_len):
    """
    name의 각 알파벳을 one_hot_vector로 인코딩
    max_seq_len까지 zero padding 추가
    """
    if not is_alpha(name):
        raise Exception("input name is not alphabet string!: " + name)

    result = []
    for char in name.lower()[:max_seq_len]:
        v = np.zeros(26, dtype=np.int)
        try:
            v[alphabet.index(char)] = 1
            result.append(v)
        except ValueError:
            pass

    while len(result) < max_seq_len:
        result.append(np.zeros(26, dtype=np.int))

    return np.array(result)


def as_keras_metric(method):
    @functools.wraps(method)
    def wrapper(self, args, **kwargs):
        """ Wrapper for turning tensorflow metrics into keras metrics """
        value, update_op = method(self, args, **kwargs)
        K.get_session().run(tf.local_variables_initializer())
        with tf.control_dependencies([update_op]):
            value = tf.identity(value)
        return value

    return wrapper


auc = {"auc": as_keras_metric(tf.metrics.AUC)}


class LSTM_Model:
    def __init__(self, model_path):
        if "korean_prob" in model_path:
            self.type = "korean_prob"
        elif "woman_prob" in model_path:
            self.type = "woman_prob"
        else:
            raise Exception("wrong model path:", model_path)

        self.model = load_model(model_path, custom_objects=auc)

    def _pred(self, string):
        return self.model.predict(name_one_hot(string, 15).reshape(1, 15, 26))[0]

    def pred(self, string):
        if self.type == "korean_prob":
            return self.korean_prob_first_name(string)
        elif self.type == "woman_prob":
            return self.woman_prob_first_name(string)
        else:
            raise Exception("wrong type:", self.type)

    def korean_prob_first_name(self, first_name):
        """
        Calculate korean_prob of first_name
        Basically the model predicts (kr/ch/en) probs.
        """

        normalized_first_name = ""
        nationalities_of_parts = set()

        max_korean_prob = 0
        max_chinese_prob = 0
        min_korean_prob = 0.5

        for _part in first_name.split():
            part = normalize(_part)
            if len(part) > 1:
                probs = self._pred(part)
                maxarg = np.argmax(probs)

                if maxarg == 0:
                    max_korean_prob = max(max_korean_prob, scale(probs[0]))
                    nationalities_of_parts.add("korean")
                elif maxarg == 1:
                    max_chinese_prob = max(max_chinese_prob, scale(probs[1]))
                    nationalities_of_parts.add("chinese")

                min_korean_prob = min(min_korean_prob, scale(probs[0]))
                normalized_first_name += part

        if len(normalized_first_name) > 1:
            probs = self._pred(normalized_first_name)
            maxarg = np.argmax(probs)

            if maxarg == 0:
                """
                If normalized first name is most likely korean,
                its prob >= 1/3 so that scale(prob) >= 1/2.
                => Classify it as korean directly. 
                """
                return scale(probs[0])

            elif maxarg == 1:
                max_chinese_prob = max(max_chinese_prob, scale(probs[1]))
                nationalities_of_parts.add("chinese")

            min_korean_prob = min(min_korean_prob, scale(probs[0]))

        if "korean" in nationalities_of_parts:
            if "chinese" in nationalities_of_parts:
                return 1 - max_chinese_prob
            else:
                return max_korean_prob
        else:
            return min_korean_prob

    def woman_prob_first_name(self, first_name):
        return self._pred(normalize(first_name))[0]
