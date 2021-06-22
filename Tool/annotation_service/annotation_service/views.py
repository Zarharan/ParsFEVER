from django.db import transaction
from django.db.models import Q
from django.template.response import TemplateResponse
from django.http import JsonResponse
import datetime
from accounts.models import User
from wf1.models import Claim
from wf2.models import ClaimState, Evidence, Label
from wiki.crawler import *
from wiki.models import Page, Sentence

MUTATIONS_TYPES = ['rephrase', 'negate', 'similar', 'dissimilar', 'specific', 'general']


def index_view(request):
    return TemplateResponse(request, 'index.html')


def work_in_progress_view(request):
    return TemplateResponse(request, 'work_in_progress.html')


def validate_textbox_view(request):
    text = request.POST.get('text', None)
    lines = text.splitlines()
    if len(lines) < 2 or len(lines) > 5:
        return JsonResponse({'is_valid': 0, 'message': 'Enter 2-5 claims!'})
    return JsonResponse({'is_valid': 1, 'message': 'OK'})


def get_user_pages_view(request):
    user_id = request.POST.get('user', None)
    pages = Page.objects.filter(user_id=user_id, status__in=[2, 3]).values('id', 'title')
    return JsonResponse({'pages': list(pages)})


@transaction.atomic
def save_mutation_view(request):
    claims = request.POST.get('claim_contents').splitlines()
    if len(claims) < 2 or len(claims) > 5:
        return JsonResponse({'is_valid': 0, 'message': 'Enter 2-5 claims!'})
    mutation_type = MUTATIONS_TYPES.index(request.POST.get('mutation_type'))
    source_claim = Claim.objects.get(id=request.POST.get('source_claim_id'))
    Claim.objects.filter(parent_claim=source_claim, mutation_type=mutation_type).delete()
    for claim in claims:
        Claim.objects.create(claim_content=claim, page=source_claim.page, mutation_type=mutation_type,
                             parent_claim=source_claim,
                             sentence=source_claim.sentence, user=request.user)
    return JsonResponse({'is_valid': 1, 'message': 'Saved successfully!'})


def statistics_update_view(request):
    start = datetime.datetime.strptime(request.POST.get('start'), '%d/%m/%Y')
    end = datetime.datetime.strptime(request.POST.get('end'), '%d/%m/%Y') + datetime.timedelta(days=1)
    context = {'rows': []}
    users = User.objects.filter()
    total_pages_count = 0
    total_main_claims_count = 0
    total_mutations_count = 0
    total_label_count = 0
    total_annotation_count = 0
    for user in users:
        main_claims_count = Claim.objects.filter(user=user, parent_claim=None, last_update__gte=start,
                                                 last_update__lt=end).count()
        mutations_count = Claim.objects.filter(Q(user=user) & Q(last_update__gte=start) &
                                               ~Q(claim_content__regex=r"\s*#\s*") &
                                               Q(last_update__lt=end) & ~Q(parent_claim=None)).count()
        pages_count = Page.objects.filter(user=user, status=3, last_update__gte=start, last_update__lt=end).count()
        label_count = Label.objects.filter(user=user, last_update__gte=start, last_update__lt=end).count()
        annotation_count = ClaimState.objects.filter(Q(user=user, last_update__gte=start,
                                                       last_update__lt=end) & ~Q(state=0)).count()
        wf1_total_count = main_claims_count + mutations_count
        wf2_total_count = label_count + annotation_count
        total_pages_count += pages_count
        total_main_claims_count += main_claims_count
        total_mutations_count += mutations_count
        total_label_count += label_count
        total_annotation_count += annotation_count
        context['rows'].append({'first_name': user.first_name, 'last_name': user.last_name,
                                'pages_count': pages_count,
                                'main_claims_count': main_claims_count,
                                'mutations_count': mutations_count,
                                'label_count': label_count,
                                'annotation_count': annotation_count,
                                'wf1_total_count': wf1_total_count,
                                'wf2_total_count': wf2_total_count,
                                'total_count': wf1_total_count + wf2_total_count})
    context['total_pages_count'] = total_pages_count
    context['total_main_claims_count'] = total_main_claims_count
    context['total_mutations_count'] = total_mutations_count
    context['total_label_count'] = total_label_count
    context['total_annotation_count'] = total_annotation_count
    context['total_wf1_count'] = total_main_claims_count + total_mutations_count
    context['total_wf2_count'] = total_label_count + total_annotation_count
    context['total_count'] = context['total_wf1_count'] + context['total_wf2_count']
    return JsonResponse(context)


@transaction.atomic
def supervisor_check_view(request):
    if not request.user.is_superuser:
        return JsonResponse({'is_valid': 0, 'message': 'Permission denied!'})
    source_claim = Claim.objects.get(id=request.POST.get('source_claim_id'))
    for field in source_claim._meta.local_fields:
        if field.name == "last_update":
            field.auto_now = False
    source_claim.checked_by_supervisor = True
    source_claim.save()
    for field in source_claim._meta.local_fields:
        if field.name == "last_update":
            field.auto_now = True
    return JsonResponse({'is_valid': 1, 'message': 'Saved successfully!'})


def get_sentence_hyperlinks_view(request):
    sentence_id = request.POST.get('sentence_id', None)
    selected_sentence = Sentence.objects.get(id=sentence_id)
    sentences = []
    hyperlinks = list(selected_sentence.hyperlinks.all().values('id', 'title', 'first_paragraph'))
    for i in range(len(hyperlinks)):
        hyperlinks[i]['background_color'] = "#eaeaea"
    if eval(request.POST.get('edit')):
        claim_id = request.POST.get('claim_id', None)
        user_id = request.POST.get('user_id', None)
        label = Label.objects.filter(claim_id=claim_id, user_id=user_id, sentence=selected_sentence)
        if label.exists() and label.first().evidence:
            label = label.first()
            for i in range(len(hyperlinks)):
                if hyperlinks[i]['id'] in [hyperlink['id'] for hyperlink in
                                           label.evidence.hyperlinks.all().values('id')]:
                    hyperlinks[i]['background_color'] = "#C5C9F9"
            pages = []
            for sentence in label.evidence.sentences.all():
                if sentence.page not in pages:
                    pages.append(sentence.page)
                    for page_sentence in sentence.page.sentences.all():
                        if page_sentence in label.evidence.sentences.all():
                            sentences.append({'id': page_sentence.id, 'page__title': page_sentence.page.title,
                                              'sentence_content': page_sentence.sentence_content,
                                              'background_color': "#C5C9F9"})
                        else:
                            sentences.append({'id': page_sentence.id, 'page__title': page_sentence.page.title,
                                              'sentence_content': page_sentence.sentence_content,
                                              'background_color': "#eaeaea"})
            for hyperlink in label.evidence.hyperlinks.filter():
                if hyperlink not in selected_sentence.hyperlinks.all():
                    hyperlinks.append({'id': hyperlink.id, 'title': hyperlink.title,
                                       'first_paragraph': hyperlink.first_paragraph, 'background_color': "#C5C9F9"})
    return JsonResponse({'hyperlinks': hyperlinks, 'sentences': sentences})


@transaction.atomic
def add_evidence_view(request):
    page_token = request.POST.get('page_token')
    selected_sentence_id = request.POST.get('selected_sentence_id')
    try:
        page = crawl_wiki_page(page_token.strip(), as_evidence=True)
    except Exception as e:
        return JsonResponse({'is_valid': False, 'message': 'Unsuccessful because !' + str(e.args)})
    if not page:
        page = Page.objects.get(token=page_token.strip())
    hyperlinks = page.hyperlinks.filter(~Q(sentences__id__in=[selected_sentence_id]))
    return JsonResponse({'is_valid': True,
                         'sentences': list(page.sentences.all().values('id', 'page__title', 'sentence_content')),
                         'hyperlinks': list(hyperlinks.values('id', 'title', 'first_paragraph'))})


@transaction.atomic
def update_claim_state_view(request):
    claim_id = request.POST.get('claim_id', None)
    state = request.POST.get('state', None)
    edit = eval(request.POST.get('edit', None))
    user_id = eval(request.POST.get('user_id', None))
    if edit:
        if request.user.id != user_id:
            return JsonResponse({'is_valid': False, 'message': 'You can\'t edit others annotation!'})
        labels = Label.objects.filter(user_id=user_id, claim_id=claim_id)
        for label in labels:
            if label.evidence:
                label.evidence.sentences.clear()
                label.evidence.hyperlinks.clear()
                label.evidence.delete()
            label.delete()
    claim_states = ClaimState.objects.filter(claim_id=claim_id, user=request.user)
    if len(claim_states) > 1:
        for i in range(1, len(claim_states)):
            claim_states[i].delete()
    claim_states[0].state = state
    claim_states[0].save()
    request.user.label_count = Label.objects.filter(user=request.user).count()
    request.user.annotation_count = ClaimState.objects.filter(Q(user=request.user) & ~Q(state=0)).count()
    request.user.save()
    return JsonResponse({'is_valid': True})


@transaction.atomic
def annotate_view(request):
    claim_id = request.POST.get('claim_id', None)
    sentence_id = request.POST.get('sentence_id', None)
    label_int = request.POST.get('label', None)
    hyperlinks_id = request.POST.getlist('hyperlinks_id[]', [])
    sentences_id = request.POST.getlist('sentences_id[]', [])
    edit = eval(request.POST.get('edit', None))
    user_id = eval(request.POST.get('user_id', None))
    if edit and user_id != request.user.id:
        return JsonResponse({'is_valid': False, 'message': 'You can\'t edit others annotation!'})
    if sentence_id in sentences_id:
        return JsonResponse({'is_valid': False, 'message': 'You can\'t select a sentence as its own evidence!'})
    suspicious_labels = Label.objects.filter(sentence_id__in=sentences_id)
    for suspicious_label in suspicious_labels:
        if suspicious_label.evidence:
            suspicious_hyperlinks_id = [hyperlink['id'] for hyperlink in
                                        suspicious_label.evidence.hyperlinks.all().values('id')]
        else:
            suspicious_hyperlinks_id = []
        if set(suspicious_hyperlinks_id) != set(map(int, hyperlinks_id)):
            continue
        if suspicious_label.evidence:
            suspicious_sentences_id = [sentence['id'] for sentence in
                                       suspicious_label.evidence.sentences.all().values('id')]
        else:
            suspicious_sentences_id = []
        suspicious_sentences_id.append(suspicious_label.sentence.id)
        if set(suspicious_sentences_id) == set(list(map(int, sentences_id))+[int(sentence_id)]):
            return JsonResponse({'is_valid': False, 'message': 'Duplicate claim label detected!'
                                                               '\n(Evidence + source sentence) set has been '
                                                               'used before!'})
    claim = Claim.objects.get(id=claim_id)
    done = False
    if edit:
        label = Label.objects.filter(claim=claim, sentence_id=sentence_id, user=user_id)
        claim_state = ClaimState.objects.get(claim=claim, user_id=user_id)
        claim_state.state = 0
        claim_state.save()
        if label.exists():
            label = label.first()
            label.label = label_int
            if label.evidence:
                label.evidence.sentences.clear()
                label.evidence.hyperlinks.clear()
                if len(hyperlinks_id) > 0:
                    label.evidence.hyperlinks.add(*hyperlinks_id)
                if len(sentences_id) > 0:
                    label.evidence.sentences.add(*sentences_id)
            elif len(hyperlinks_id) + len(sentences_id) > 0:
                evidence = Evidence.objects.create()
                if len(hyperlinks_id) > 0:
                    evidence.hyperlinks.add(*hyperlinks_id)
                if len(sentences_id) > 0:
                    evidence.sentences.add(*sentences_id)
                label.evidence = evidence
            label.save()
            done = True
    if not done:
        evidence = None
        if len(hyperlinks_id) + len(sentences_id) > 0:
            evidence = Evidence.objects.create()
            if len(hyperlinks_id) > 0:
                evidence.hyperlinks.add(*hyperlinks_id)
            if len(sentences_id) > 0:
                evidence.sentences.add(*sentences_id)
        label = Label.objects.create(claim=claim, sentence_id=sentence_id, label=label_int,
                                     user=request.user, evidence=evidence)
    request.user.label_count = Label.objects.filter(user=request.user).count()
    request.user.annotation_count = ClaimState.objects.filter(Q(user=request.user) & ~Q(state=0)).count()
    request.user.save()
    return JsonResponse({'is_valid': True})


@transaction.atomic
def submit_wf2_view(request):
    claim_id = request.POST.get('claim_id', None)
    flag = request.POST.get('flag', None)
    claim = Claim.objects.get(id=claim_id)
    edit = eval(request.POST.get('edit', None))
    user_id = eval(request.POST.get('user_id', None))
    if edit and user_id != request.user.id:
        return JsonResponse({'is_valid': False, 'message': 'You can\'t edit others annotation!'})
    if claim.labels.count() > 0:
        claim_states = ClaimState.objects.filter(claim_id=claim_id, user=request.user)
        if len(claim_states) > 1:
            for i in range(1, len(claim_states)):
                claim_states[i].delete()
        claim_states[0].state = 6 - int(flag)    # if flag state = 5 else finish state = 6
        request.user.label_count = Label.objects.filter(user=request.user).count()
        request.user.annotation_count = ClaimState.objects.filter(Q(user=request.user) & ~Q(state=0)).count()
        request.user.save()
        claim_states[0].save()
        return JsonResponse({'is_valid': True})
    else:
        return JsonResponse({'is_valid': False, 'message': 'Generate at least one label to submit!'})


def get_user_completed_claims_view(request):
    user_id = request.POST.get('user')
    if request.POST.get('flag') == 'true':
        user_completed_claims_id = [claim_id['claim_id'] for claim_id in
                                    ClaimState.objects.filter(user_id=user_id, state=5).values('claim_id')]
    else:
        user_completed_claims_id = [claim_id['claim_id'] for claim_id in
                                    ClaimState.objects.filter(Q(user_id=user_id) & ~Q(state=0) &
                                                              ~Q(state=5)).values('claim_id')]
    claims = Claim.objects.filter(id__in=user_completed_claims_id).values('id', 'claim_content')
    return JsonResponse({'claims': list(claims)})


@transaction.atomic
def delete_label_view(request):
    claim_id = request.POST.get('claim_id', None)
    sentence_id = request.POST.get('sentence_id', None)
    edit = eval(request.POST.get('edit', None))
    user_id = eval(request.POST.get('user_id', None))
    if edit:
        if request.user.id != user_id:
            return JsonResponse({'is_valid': False, 'message': 'You can\'t edit others annotation!'})
        labels = Label.objects.filter(user_id=user_id, claim_id=claim_id, sentence_id=sentence_id)
        for label in labels:
            if label.evidence:
                label.evidence.sentences.clear()
                label.evidence.hyperlinks.clear()
                label.evidence.delete()
            label.delete()
        request.user.label_count = Label.objects.filter(user=request.user).count()
        request.user.annotation_count = ClaimState.objects.filter(Q(user=request.user) & ~Q(state=0)).count()
        request.user.save()
        return JsonResponse({'is_valid': True})
    else:
        return JsonResponse({'is_valid': False, 'message': 'Enter review mode to edit!'})


@transaction.atomic
def edit_claim_view(request):
    claim_id = request.POST.get('claim_id', None)
    claim_content = request.POST.get('claim_content', None)
    edit = eval(request.POST.get('edit', None))
    if edit:
        claim = Claim.objects.get(id=claim_id)
        claim.claim_content = claim_content.strip()
        claim.save()
        return JsonResponse({'is_valid': True, 'message': 'Claim edited successfully!'})
    else:
        return JsonResponse({'is_valid': False, 'message': 'Enter review mode to edit!'})
