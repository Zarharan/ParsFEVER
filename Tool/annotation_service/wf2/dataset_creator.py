import sys
sys.path.insert(1, './')
import django
from django.conf import settings
import annotation_service.settings as app_settings

settings.configure(INSTALLED_APPS=app_settings.INSTALLED_APPS, DATABASES=app_settings.DATABASES)
django.setup()
from wf1.models import Claim
from wf2.models import Label, ClaimState
import json, jsonlines

print("Running...")
used_pages = set()
labels = Label.objects.order_by("id")
used_hyperlinks = set()

for label in labels:
    used_pages.add(label.claim.page)
    used_pages.add(label.sentence.page)
    if not label.evidence:
        continue
    hyperlinks = label.evidence.hyperlinks.order_by("id")
    sentences = label.evidence.sentences.order_by("id")
    for hyperlink in hyperlinks:
        used_hyperlinks.add(hyperlink)
    for sentence in sentences:
        used_pages.add(sentence.page)

not_enough_info_claims = ClaimState.objects.filter(state=1).order_by("id")
for not_enough_info_claim in not_enough_info_claims:
    used_pages.add(not_enough_info_claim.claim.page)

wiki_pages = []
for used_page in used_pages:
    page = {"id": used_page.token, "text": used_page.page_content, "lines": ""}
    sentence_number = 0
    for sentence in used_page.sentences.order_by("id"):
        page["lines"] += f'{sentence_number}\t{sentence.sentence_content}\n'
        sentence_number += 1
    page["lines"] += f'{sentence_number}\t'
    wiki_pages.append(page)

for used_hyperlink in used_hyperlinks:
    hyperlink = {"id": f"hyperlink_{used_hyperlink.token}", "text": used_hyperlink.first_paragraph,
                 "lines": f"0\t{used_hyperlink.first_paragraph}\n1\t"}
    wiki_pages.append(hyperlink)

with open('wiki_pages.json', 'w', encoding='utf8') as f:
    json.dump(wiki_pages, f)

with jsonlines.open('wiki_pages.jsonl', mode='w') as writer:
    for wiki_page in wiki_pages:
        writer.write(wiki_page)

print(f'Number of used pages: {len(used_pages)}')
print(f'Number of used hyperlinks: {len(used_hyperlinks)}')

dataset = []
claims = Claim.objects.order_by("id")
for claim in claims:
    if len(claim.claim_state.all()) == 0:
        continue
    state = claim.claim_state.order_by("id").first().state
    if state == 1:
        claim_json = {"id": claim.id, "verifiable": "NOT VERIFIABLE", "label": "NOT ENOUGH INFO",
                                      "claim": claim.claim_content, "claim_page_id": claim.page.id,
                                      "claim_page_token": claim.page.token,
                                      "evidence": [[[claim.page.id, None, None, None]]]}
        dataset.append(claim_json)
    elif state == 6:
        claim_json_supports = {"id": claim.id, "verifiable": "VERIFIABLE", "label": "SUPPORTS",
                               "claim": claim.claim_content, "claim_page_id": claim.page.id,
                               "claim_page_token": claim.page.token, "evidence": []}
        claim_json_refutes = {"id": claim.id, "verifiable": "VERIFIABLE", "label": "REFUTES",
                              "claim": claim.claim_content,  "claim_page_id": claim.page.id,
                              "claim_page_token": claim.page.token, "evidence": []}
        supports = 0
        refutes = 0
        for label in claim.labels.order_by("id"):
            evidences = [[claim.page.id, label.id, label.sentence.page.token,
                          list(label.sentence.page.sentences.order_by("id")).index(label.sentence)]]
            if label.evidence:
                for label_sentence in label.evidence.sentences.order_by("id"):
                    evidences.append([claim.page.id, label.id, label_sentence.page.token,
                                      list(label_sentence.page.sentences.order_by("id")).index(label_sentence)])
                for label_hyperlink in label.evidence.hyperlinks.order_by("id"):
                    evidences.append([claim.page.id, label.id, f"hyperlink_{label_hyperlink.token}", 0])
            if label.label == 0:
                claim_json_supports["evidence"].append(evidences)
                supports += 1
            else:
                claim_json_refutes["evidence"].append(evidences)
                refutes += 1
        if supports > 0:
            dataset.append(claim_json_supports)
        if refutes > 0:
            dataset.append(claim_json_refutes)

with open('dataset.json', 'w', encoding='utf8') as f:
    json.dump(dataset, f)

with jsonlines.open('dataset.jsonl', mode='w') as writer:
    for label in dataset:
        writer.write(label)

print(f'Dataset length: {len(dataset)}')
print('Done!')
