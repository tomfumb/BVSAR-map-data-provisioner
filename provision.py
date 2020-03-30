import argparse
import os
import yaml

from provisioners.CanvecEn import CanvecEn

SRC_CANVEC_EN='canvec_en'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('minX', type = float, help = 'Lower left x value, longitude')
    parser.add_argument('minY', type = float, help = 'Lower left y value, latitude')
    parser.add_argument('maxX', type = float, help = 'Upper right x value, longitude')
    parser.add_argument('maxY', type = float, help = 'Upper right y value, latitude')
    parser.add_argument('src', type = str, help = 'Data source name')
    parser.add_argument('--dev', default = False, const = True, dest='dev', action='store_const', help = 'Whether to execute in dev mode (Python executing outside Docker container)')
    args = vars(parser.parse_args())
    if args['minX'] >= args['maxX'] or args['minY'] >= args['maxY']:
       	print('Min / max bounds are invalid. Min values must not equal or exceed max values')
        exit(1)

    ### truncate values to reasonable precision, don't want outrageously long file / project names for this

    ### additional parameter can have create, replace, continue and determines what happens if the provisioning has already occurred

    ### add logging library to better control log granularity

    ##### configuration yaml for tilemill at least, default simply provides docker-local URL but non-default says
    ##### remote docker and provides container name and copy path - referenced in TileMillManager to copy files and generate paths for project

    if args['dev']:
        configFileName = 'dev'
    else:
        configFileName = 'prod'
    configPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', configFileName + '.yaml')
    with open(configPath, 'r') as configFile:
        config = yaml.safe_load(configFile)

    if args['src'] == SRC_CANVEC_EN:
        provisioner = CanvecEn()
        provisioner.provision( \
            args['minX'], \
            args['minY'], \
            args['maxX'], \
            args['maxY'], \
            os.path.join( \
                os.path.dirname(os.path.abspath(__file__)), \
                'output', \
                ''.join(( \
                    ','.join(map(lambda flt: str(flt), (args['minX'], args['minY'], args['maxX'], args['maxY']))), \
                    '_', \
                    args['src'] \
                )) \
            ), \
            config \
        )

if __name__ == '__main__':
    main()
