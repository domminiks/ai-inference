from flask import jsonify


def pre_process(input_):
    return input_


def post_process(output):
    return {"value": float(output[0][0][0])}
