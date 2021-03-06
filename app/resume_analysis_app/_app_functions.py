import requests
import json
import operator
from random import randint
from statistics import mean
from datetime import datetime
from django.db.models import Q
from functools import reduce

# Option to discount insights below a certain relevance
keyword_relevance_boundary = 0
category_score_boundary = 0
concept_relevance_boundary = 0

# Lowest number of keywords required to consider an applicant to be recommended
kw_req_boundary = 3


def create_CVs():

    with open('resume_text/_resume_template.txt') as f:
        CV_text = f.read()

    features = {'professional_profile': 1, 'degrees': 1, 'universities': 1, 'jobs': 3, 'skills': 3}
    tags = ['# PP #', '# ED #', '# UNI #', '# WE #', '# TE #']
    for feature, amount in features.items():
        with open('resume_text/' + feature + '.txt') as file:
            contents = file.read()
            text, texts = '', []
            if '#' not in contents:
                texts = contents.split('\n')
            else:
                for line in contents:
                    if '#' in line:
                        texts.append(text)
                        text = ''
                        continue
                    text += line

            while len(texts) > amount:
                del texts[randint(0, len(texts)-1)]

            # print(texts)
            CV_text = CV_text.replace(tags[0], '\n'.join(texts))
            del tags[0]

    return CV_text


if __name__ == '__main__':
    if input('generate 20 CVs? (y): ') == 'y':
        for i in range(20):
            text = create_CVs()
            with open('resume_text/CVs/CV_' + str(i) + '.txt', 'w') as file:
                file.write(text)
else:
    from .models import Account


def extract_insights(text):
    """
    :param text: plain text taken in to be analysed for insights.
    :return:
        :keywords   : dictionary of { 'keyword' : count }
        :categories : list of [cat1, cat2, cat3]
        :concpets   : dictionary of { 'concept' : source link }
    """
    # Call NodeRED to access Watson
    url = 'https://resume-node-red.mybluemix.net/CV'
    response = requests.post(url, data=text.encode('ascii', errors='ignore')).json()

    # Select all proper nouns and capitalised nouns from text
    # Take into account strings of multiple proper nouns
    temp_keywords = []
    common_PROPN = 'JanuaryFebruaryMarchAprilMayJuneJulyAugustSeptemberOctoberNovemberDecemberABCDEFGCSEsReferences'
    prev = None
    for word in response['syntax']['tokens']:
        if word['part_of_speech'] == 'PROPN' or (
                word['part_of_speech'] == 'NOUN' and word['text'][0].isupper()):
            if prev and word['text'].lower() in common_PROPN.lower():
                temp_keywords.append(prev)
            elif word['text'].lower() in common_PROPN.lower():
                continue
            elif prev:
                prev += ' ' + word['text']
                temp_keywords.append(prev)
            else:
                temp_keywords.append(word['text'])
                prev = word['text']
        else:
            prev = None

    i = 0  # Check for consecutive keywords which may be related e.g. Amazon Web Services
    while i + 1 < len(temp_keywords):
        if temp_keywords[i] in temp_keywords[i + 1]:
            del temp_keywords[i]
        else:
            i += 1

    # Reformat list of proper nouns to be a dictionary of counts
    keywords = {}
    for kw in temp_keywords:
        if kw not in common_PROPN:
            keywords[kw] = text.count(kw)

    # Add in IBM's insights
    for kw in response['keywords']:
        if kw['relevance'] > keyword_relevance_boundary:
            keywords[kw['text']] = kw['count']

    categories = []
    for cat in response['categories']:
        if cat['score'] > category_score_boundary and len(categories) < 3:
            categories.append(cat['label'])

    concepts = {}
    for con in response['concepts']:
        if con['relevance'] > concept_relevance_boundary:
            concepts[con['text']] = con['dbpedia_resource']

    return keywords, categories, concepts


def update_applicants(job):
    print('\nUPDATING APPLICANTS')
    # For each category search for 1 category above most specific category
    # (unless lower specificity category)
    cat1 = job.category1.split('/')
    if len(cat1)>3: cat1 = "/".join(cat1[:-1])
    else: cat1 = "/".join(cat1)

    cat2 = job.category2.split('/')
    if len(cat2)>3: cat2 = "/".join(cat2[:-1])
    else: cat2 = "/".join(cat2)

    cat3 = job.category3.split('/')
    if len(cat3)>3: cat3 = "/".join(cat3[:-1])
    else: cat3 = "/".join(cat3)

    # Exclude with jobs already
    cat1_matches = Account.objects.filter(
        category1__contains=cat1).exclude(job__isnull=False) | Account.objects.filter(
        category2__contains=cat1).exclude(job__isnull=False) | Account.objects.filter(
        category3__contains=cat1).exclude(job__isnull=False)

    cat2_matches = Account.objects.filter(
        category1__contains=cat2).exclude(job__isnull=False) | Account.objects.filter(
        category2__contains=cat2).exclude(job__isnull=False) | Account.objects.filter(
        category3__contains=cat2).exclude(job__isnull=False)

    cat3_matches = Account.objects.filter(
        category1__contains=cat3).exclude(job__isnull=False) | Account.objects.filter(
        category2__contains=cat3).exclude(job__isnull=False) | Account.objects.filter(
        category3__contains=cat3).exclude(job__isnull=False)

    # Give each use points for how many times they appear in the lists
    # More points for getting a more relevant category
    cat_matches = {}
    for match in cat1_matches:
        if match in cat_matches.keys():
            cat_matches[match] += 3
        else:
            cat_matches[match] = 3

    for match in cat2_matches:
        if match in cat_matches.keys():
            cat_matches[match] += 2
        else:
            cat_matches[match] = 2

    for match in cat3_matches:
        if match in cat_matches.keys():
            cat_matches[match] += 1
        else:
            cat_matches[match] = 1

    # Sort by number of matches found
    cat_matches = {k: v for k, v in sorted(cat_matches.items(), reverse=True, key=lambda item: item[1])}
    cat_matches = list(cat_matches.keys())
    print('matches:', cat_matches)

    i, job_kws = 0, job.keywords_req
    while i != len(cat_matches):
        # Remove if no keywords - no resume uploaded!
        if cat_matches[i].keywords == '{}':
            del cat_matches[i]
            continue
        # Remove if no personality - interview no answered!
        if cat_matches[i].pers_big5 == '{}':
            del cat_matches[i]
            continue
        # If candidate doesn't have every required keyword
        candidate_kws = ' '.join(json.loads(cat_matches[i].keywords).keys())
        for kw in job_kws:
            if kw not in candidate_kws:
                del cat_matches[i]
                break
        else: i += 1

    job.recommended.clear()
    for match in cat_matches:
        print(f'adding {match} to  recommendations')
        job.recommended.add(match.user)


def update_aggregate_personality(job):

    emps = Account.objects.filter(job=job).exclude(pers_big5='').all()
    if len(emps) == 0: return

    # Lays out keys with a list in each
    aggr_big5 = {k: [] for k, v in json.loads(emps[0].pers_big5).items()}
    aggr_openness = {k: [] for k, v in json.loads(emps[0].pers_openness).items()}
    aggr_conscien = {k: [] for k, v in json.loads(emps[0].pers_conscien).items()}
    aggr_agreeabl = {k: [] for k, v in json.loads(emps[0].pers_agreeabl).items()}
    aggr_extraver = {k: [] for k, v in json.loads(emps[0].pers_extraver).items()}
    aggr_em_range = {k: [] for k, v in json.loads(emps[0].pers_em_range).items()}
    aggr_needs = {k: [] for k, v in json.loads(emps[0].needs).items()}
    aggr_values = {k: [] for k, v in json.loads(emps[0].values).items()}

    cur_year = datetime.now().year
    # For each employee, append the value to the list
    for emp in emps:
        pers_big5 = json.loads(emp.pers_big5)
        pers_openness = json.loads(emp.pers_openness)
        pers_conscien = json.loads(emp.pers_conscien)
        pers_agreeabl = json.loads(emp.pers_agreeabl)
        pers_extraver = json.loads(emp.pers_extraver)
        pers_em_range = json.loads(emp.pers_em_range)
        pers_needs = json.loads(emp.needs)
        pers_values = json.loads(emp.values)

        # For n years they have been at the position
        # count their personality n^2 times (higher weighting
        # to those who stay longer predicts retention)
        for _ in range(1+(cur_year-emp.job_start)**2):
            aggr_big5 = {k: v+[pers_big5[k]] for k, v in aggr_big5.items()}
            aggr_openness = {k: v+[pers_openness[k]] for k, v in aggr_openness.items()}
            aggr_conscien = {k: v+[pers_conscien[k]] for k, v in aggr_conscien.items()}
            aggr_agreeabl = {k: v+[pers_agreeabl[k]] for k, v in aggr_agreeabl.items()}
            aggr_extraver = {k: v+[pers_extraver[k]] for k, v in aggr_extraver.items()}
            aggr_em_range = {k: v+[pers_em_range[k]] for k, v in aggr_em_range.items()}
            aggr_needs = {k: v+[pers_needs[k]] for k, v in aggr_needs.items()}
            aggr_values = {k: v+[pers_values[k]] for k, v in aggr_values.items()}

    # Replace the lists of values with the mean of the list
    job.aggr_big5 = json.dumps({k: mean(v) for k, v in aggr_big5.items()})
    job.aggr_openness = json.dumps({k: mean(v) for k, v in aggr_openness.items()})
    job.aggr_conscien = json.dumps({k: mean(v) for k, v in aggr_conscien.items()})
    job.aggr_agreeabl = json.dumps({k: mean(v) for k, v in aggr_agreeabl.items()})
    job.aggr_extraver = json.dumps({k: mean(v) for k, v in aggr_extraver.items()})
    job.aggr_em_range = json.dumps({k: mean(v) for k, v in aggr_em_range.items()})
    job.needs = json.dumps({k: mean(v) for k, v in aggr_needs.items()})
    job.values = json.dumps({k: mean(v) for k, v in aggr_values.items()})

    job.save()

    # return to dict
    job.keywords = json.loads(job.keywords)
    job.concepts = json.loads(job.concepts)


def custom_search(categories, keywords, job=None):
    """
    Allows for search for all given key terms.
    :param categories: ['LAYER1/LAYER2/LAYER3', 'LAYER1']
    :param keywords: ['kw1', 'kw2', 'kw3']
    :return: list of candidates with the required keywords.
    """
    candidates = []
    if len(categories) != 0:
        for cat in categories:
            # Exclude those with jobs already
            candidates.append(Account.objects.filter(
                category1__contains=cat).exclude(job__isnull=False) | Account.objects.filter(
                category2__contains=cat).exclude(job__isnull=False) | Account.objects.filter(
                category3__contains=cat).exclude(job__isnull=False))
        # Reduce dimensionality of list
        candidates = [x for ls in candidates for x in ls]
        # If x categories provided candidate must be returned by x queries so appear x times in the list
        candidates = [x for x in candidates if candidates.count(x) == len(categories)]
        # Filter out where keywords not present
        for kw in keywords:
            candidates = [x for x in candidates if kw in x.keywords]

    # No categories selected, search for keywords
    elif len(keywords) != 0:
        candidates = Account.objects.filter(reduce(operator.and_, (Q(keywords__icontains='"'+x+'"') for x in keywords)))

    # Candidates got, now sort
    if job:
        candidates = [x for x in candidates if x.user not in job.removed.all()]
    return candidates
