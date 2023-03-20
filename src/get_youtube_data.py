import sys
import langid
import pandas as pd

# a code youtubeReviewsInLanguages.py by Raghvendra Pratap Singh
# M.Sc. student, Dublin City University, Ireland, 2019-20
#
#usage:
#python3 youtubeReviewsInLanguages.py <input json file> <two letter language> <output.csv>
#
#example:
#python3 youtubeReviewsInLanguages.py json_files/input.json hi outputs_dir/output.csv

jsonfileValue = sys.argv[1]

data = pd.read_json(jsonfileValue, lines=True)
df = pd.DataFrame(data)
df2 = pd.DataFrame(columns=['text'], data=df[['text']].values)
list = []
count = 0
ListOfLanguages = ['af','am','an','ar','as','az','be','bg','bn','br','bs','ca','cs','cy','da','de','dz','el','en','eo','es','et','eu','fa','fi','fo','fr','ga','gl','gu','he','hi','hr','ht','hu','hy','id','is','it','ja','jv','ka','kk','km','kn','ko','ku','ky','la','lb','lo','lt','lv','mg','mk','ml','mn','mr','ms','mt','nb','ne','nl','nn','no','oc','or','pa','pl','ps','pt','qu','ro','ru','rw','se','si','sk','sl','sq','sr','sv','sw','ta','te','th','tl','tr','ug','uk','ur','vi','vo','wa','xh','zh','zu']

if len(sys.argv[2])==2:
    if sys.argv[2] in ListOfLanguages:
        # Strips the newline character
        for index, row in df2.iterrows():
            a = langid.classify(str(row))
            if a[0]==sys.argv[2]:
                list.append(row)
    else:
        print("Please check https://pypi.org/project/langid/1.1dev/ and if your input language is available there, add it to ListOfLanguages")
else:
    print("please enter the language with length of 2 characters")
    sys.exit()


df3 = pd.DataFrame(list)
df3.to_csv(sys.argv[3], encoding='utf-8')