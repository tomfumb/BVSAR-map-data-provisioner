import logging

def bboxArgsValidator(argsDict):
    logger = logging.getLogger(__name__)
    minX = float(argsDict.get('minX', 1))
    minY = float(argsDict.get('minY', 1))
    maxX = float(argsDict.get('maxX', -1))
    maxY = float(argsDict.get('maxY', -1))
    logger.debug('validating minX: %f, minY: %f, maxX: %f, maxY: %f', minX, minY, maxX, maxY)

    if minX >= maxX or minY >= maxY:
        raise ValueError('Min / max bounds are invalid. Min values must not equal or exceed max values (crossing IDL is not supported)')