import re
import logging

def bboxArgsValidator(argsDict, required = True):
    minXString = argsDict.get('minX', None)
    minYString = argsDict.get('minY', None)
    maxXString = argsDict.get('maxX', None)
    maxYString = argsDict.get('maxY', None)
    logging.debug('validating minX: %s, minY: %s, maxX: %s, maxY: %s', minXString, minYString, maxXString, maxYString)

    for stringArg in (minXString, minYString, maxXString, maxYString):
        if stringArg == None and required:
            logging.warn('Required value(s) not provided for bbox')
            raise ValueError('minX, minY, maxX, maxY values are all required')
        if re.match(r'^(\-)?\d{1,3}(\.\d+)?$', stringArg) == None:
            raise ValueError('Incorrect value format "%s" for bbox. Must be Lat/Long', stringArg)

    minX, minY, maxX, maxY = float(minXString), float(minYString), float(maxXString), float(maxYString)

    if minX >= maxX or minY >= maxY:
        raise ValueError('Min / max bounds are invalid. Min values must not equal or exceed max values (crossing IDL is not supported)')