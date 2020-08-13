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
        """
        Calculate korean_female_prob of korean first_name
        """
        return self._pred(normalize(first_name))[0]

    def build_model(self):
        model = Sequential()
        model.add(Bidirectional(LSTM(64, input_shape=(15, 26))))
        model.add(Dense(3, activation="softmax", kernel_initializer="normal"))
        model.compile(
            loss="categorical_crossentropy",
            optimizer=Adam(0.0005),
            metrics=["accuracy", as_keras_metric(tf.metrics.auc)],
        )
        self.model = model

    def show_train_graph(self, hist):
        fig, loss_ax = plt.subplots()
        acc_ax = loss_ax.twinx()

        loss_ax.plot(hist.history["loss"], "y", label="train loss")
        loss_ax.plot(hist.history["val_loss"], "r", label="val loss")

        acc_ax.plot(hist.history["acc"], "b", label="train acc")
        acc_ax.plot(hist.history["val_acc"], "g", label="val acc")

        acc_ax.plot(hist.history["auc"], "m", label="train auc")
        acc_ax.plot(hist.history["val_auc"], "k", label="val auc")

        loss_ax.set_xlabel("epoch")
        loss_ax.set_ylabel("loss")
        acc_ax.set_ylabel("auc_roc")

        loss_ax.legend(loc="upper left")
        acc_ax.legend(loc="lower left")

        plt.show()
        fig.savefig("./static/data/train_graph.png")

    def train_korean_prob_model(self):
        # ------------------------------------
        max_seq_len = 15
        np.random.seed(5)
        # ------------------------------------

        kr_list = get_file("./static/data/kr_first_names.txt")
        ch_list = get_file("./static/data/ch_first_names.txt")
        us_list = get_file("./static/data/us_first_names.txt")

        a = len(kr_list)
        b = len(ch_list)
        c = len(us_list)
        data_len = a + b + c

        X, Y = [], []

        for _ in range(1):
            for name in kr_list:
                X.append(name_one_hot(name, max_seq_len))
                Y.append(np.array([1, 0, 0]))
        for _ in range(1):
            for name in ch_list:
                X.append(name_one_hot(name, max_seq_len))
                Y.append(np.array([0, 1, 0]))
        for name in us_list:
            X.append(name_one_hot(name, max_seq_len))
            Y.append(np.array([0, 0, 1]))

        X, Y = np.array(X), np.array(Y)

        np.reshape(X, (data_len, max_seq_len, 26))
        np.reshape(Y, (data_len, 1, 3))

        permutation = np.random.permutation(X.shape[0])
        X = X[permutation]
        Y = Y[permutation]

        train_len = int(data_len * 0.99)

        x_train = X[:train_len]
        y_train = Y[:train_len]
        x_val = X[train_len:]
        y_val = Y[train_len:]

        loss_CP = ModelCheckpoint(
            "./static/temp/loss.h5",
            monitor="val_loss",
            mode="min",
            verbose=0,
            save_best_only=True,
        )
        acc_CP = ModelCheckpoint(
            "./static/temp/acc.h5",
            monitor="val_acc",
            mode="max",
            verbose=0,
            save_best_only=True,
        )
        auc_CP = ModelCheckpoint(
            "./static/temp/auc.h5",
            monitor="val_auc",
            mode="max",
            verbose=0,
            save_best_only=True,
        )

        self.build_model()
        model = self.model
        hist = model.fit(
            x_train,
            y_train,
            epochs=300,
            batch_size=512,
            validation_data=(x_val, y_val),
            verbose=2,
            callbacks=[loss_CP, acc_CP, auc_CP],
        )

        # score = model.evaluate(x_test, y_test)
        # print("%s: %.2f%%" %(model.metrics_names[1], score[1] * 100))

        # model.save(self.model_path)
        self.show_train_graph(hist)

    # def train_woman_prob_model(self):
    #     # ------------------------------------
    #     max_seq_len = 15
    #     np.random.seed(5)
    #     # ------------------------------------
    #     # 
    #     names_by_gender = json.load(open("./names_by_gender.json"))

    #     female_list = names_by_gender["female"]
    #     male_list = names_by_gender["male"]

    #     a = len(female_list)
    #     b = len(male_list)

    #     data_len = a + b

    #     X, Y = [], []

    #     for _ in range(1):
    #         for name in female_list:
    #             X.append(name_one_hot(name, max_seq_len))
    #             Y.append(np.array([1, 0]))
    #     for _ in range(1):
    #         for name in male_list:
    #             X.append(name_one_hot(name, max_seq_len))
    #             Y.append(np.array([0, 1]))

    #     X, Y = np.array(X), np.array(Y)

    #     np.reshape(X, (data_len, max_seq_len, 26))
    #     np.reshape(Y, (data_len, 1, 2))

    #     permutation = np.random.permutation(X.shape[0])
    #     X = X[permutation]
    #     Y = Y[permutation]

    #     train_len = int(data_len * 0.99)

    #     x_train = X[:train_len]
    #     y_train = Y[:train_len]
    #     x_val = X[train_len:]
    #     y_val = Y[train_len:]

    #     loss_CP = ModelCheckpoint(
    #         "./model/gender_loss.h5",
    #         monitor="val_loss",
    #         mode="min",
    #         verbose=0,
    #         save_best_only=True,
    #     )
    #     acc_CP = ModelCheckpoint(
    #         "./model/gender_acc.h5",
    #         monitor="val_acc",
    #         mode="max",
    #         verbose=0,
    #         save_best_only=True,
    #     )
    #     auc_CP = ModelCheckpoint(
    #         "./model/gender_auc.h5",
    #         monitor="val_auc",
    #         mode="max",
    #         verbose=0,
    #         save_best_only=True,
    #     )

    #     self.build_model()
    #     model = self.model
    #     hist = model.fit(
    #         x_train,
    #         y_train,
    #         epochs=100,
    #         batch_size=512,
    #         validation_data=(x_val, y_val),
    #         verbose=2,
    #         callbacks=[loss_CP, acc_CP, auc_CP],
    #     )

    #     # score = model.evaluate(x_test, y_test)
    #     # print("%s: %.2f%%" %(model.metrics_names[1], score[1] * 100))

    #     # model.save(self.model_path)
    #     self.show_train_graph(hist)
