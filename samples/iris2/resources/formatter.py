from flask import jsonify

irises = {
    0: "Iris Setosa",
    1: "Iris Virginica",
    2: "Iris Versicolor"
}


def pre_process(input_):
    return input_


def post_process(output):
    return {"iris": irises[int(output[0][0])]}
