import pyproj

from provisioners.Provisioner import Provisioner

class CanvecEn(Provisioner):

    destCrs = None
    dpi = 96
    maxW = 4096
    maxH = 4096
    scales = (250000,150000,70000,35000)

    def __init__(self):
        self.destCrs = pyproj.Proj("+init=EPSG:3857")

    def provision(self, minX, minY, maxX, maxY, outputDirectory):
        ll = pyproj.transform(self.srcCrs, self.destCrs, minX, minY)
        ur = pyproj.transform(self.srcCrs, self.destCrs, maxX, maxY)
        metres = (ur[0] - ll[0], ur[1] - ll[1])
        inches = (metres[0] / self.metresPerInch, metres[1] / self.metresPerInch)
        pixelsAtScale = (inches[0] * self.dpi, inches[1] * self.dpi)
        pixelsAtScales = list(map(lambda scale: list(map(lambda pixelValue: pixelValue / scale, pixelsAtScale)), self.scales))

        for idx, scale in enumerate(self.scales):
            print (str(scale) + ': ' + ','.join(list(map(lambda num: str(num), pixelsAtScales[idx]))))
