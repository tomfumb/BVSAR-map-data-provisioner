import argparse

from provisioners.CanvecEn import CanvecEn

SRC_CANVEC_EN='canvec_en'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("minX", type=float, help='Lower left x value, longitude')
    parser.add_argument("minY", type=float, help='Lower left y value, latitude')
    parser.add_argument("maxX", type=float, help='Upper right x value, longitude')
    parser.add_argument("maxY", type=float, help='Upper right y value, latitude')
    parser.add_argument("--src", choices=[SRC_CANVEC_EN], default=SRC_CANVEC_EN)
    args = vars(parser.parse_args())
    if args["minX"] >= args["maxX"] or args["minY"] >= args["maxY"]:
       	print("Min / max bounds are invalid. Min values must not equal or exceed max values")
        exit(1)
    if args["src"] == SRC_CANVEC_EN:
        provisioner = CanvecEn()
        provisioner.provision(args["minX"], args["minY"], args["maxX"], args["maxY"], "out location")

if __name__ == '__main__':
    main()
