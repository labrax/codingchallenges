import glob
import subprocess

FILES = glob.glob('*.csv')

for f, index in zip(FILES, range(len(FILES))):
    print(f, index)
    with open('arq{}.in'.format(index), 'w') as infile:
        infile.write(f + '\n')
    p = subprocess.Popen("cat arq{}.in | Rscript solve.R > arq{}.res".format(index, index), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = p.communicate()
    print(c)
