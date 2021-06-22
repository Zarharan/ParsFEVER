from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from wf1.models import Claim
from wf2.forms import Wf2Form, CheckSentencesForm, WF2ReviewForm
from django.db.models import Q
from wf2.models import ClaimState, Label, CLAIM_STATES
from wiki.crawler import get_wiki_information, get_hyperlink_information
from wiki.models import Page, Sentence, Hyperlink


class CheckSentencesView(View):
    form_class = CheckSentencesForm
    template_name = 'check-sentences.html'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        with open('page_tokens_to_check.txt', encoding='utf-8') as page_tokens_to_check_file:
            page_tokens_to_check = [page_token.strip() for page_token in page_tokens_to_check_file.readlines()]
        with open('checked_page_tokens.txt', encoding='utf-8') as checked_page_tokens_file:
            checked_page_tokens = [page_token.strip() for page_token in checked_page_tokens_file.readlines()]
        with open('skipped_page_tokens.txt', encoding='utf-8') as skipped_page_tokens_file:
            skipped_page_tokens = [page_token.strip() for page_token in skipped_page_tokens_file.readlines()]
        first_unchecked_page_token_index = 0
        while page_tokens_to_check[first_unchecked_page_token_index] in checked_page_tokens or \
                page_tokens_to_check[first_unchecked_page_token_index] in skipped_page_tokens:
            first_unchecked_page_token_index += 1
            if first_unchecked_page_token_index >= len(checked_page_tokens) or \
                    first_unchecked_page_token_index >= len(skipped_page_tokens):
                return redirect(reverse('index'))
        page_token_to_check = page_tokens_to_check[first_unchecked_page_token_index]
        _, _, crawled_introductory, crawled_html, crawled_sentences = get_wiki_information(page_token_to_check)
        page_to_check = Page.objects.get(token=page_token_to_check)
        try:
            source_sentence = page_to_check.claims.first().sentence
        except:
            with open('skipped_page_tokens.txt', 'a+', encoding='utf-8') as skipped_page_tokens_file:
                skipped_page_tokens_file.write(page_to_check.token+'\n')
            return redirect(reverse('check_sentences'))
        check_sentence_form = self.form_class(sentences=[(sentence+' | دیکشنری‌مروبطه: '+str(hyperlinks),
                                                          sentence+' | دیکشنری‌مروبطه: '+str(hyperlinks))
                                                         for sentence, hyperlinks in crawled_sentences.items()],
                                              initial={'page_id': page_to_check.id, 'crawled_html': crawled_html,
                                                       'source_sentence': source_sentence})
        context = {
            'page': page_to_check,
            'source_sentence_id': source_sentence.id,
            'form': check_sentence_form
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect(reverse('index'))
        action = request.POST.get('action')
        if action == 'Home':
            return redirect(reverse('index'))
        elif action == 'Only Save HTML':
            page = Page.objects.get(id=request.POST.get('page_id'))
            page.page_content_html = request.POST.get('crawled_html')
            page.save()
            with open('checked_page_tokens.txt', 'a+', encoding='utf-8') as checked_page_tokens_file:
                checked_page_tokens_file.write(page.token+'\n')
            return redirect(reverse('check_sentences'))
        elif action == 'Update Sentences and Save HTML':
            page = Page.objects.get(id=request.POST.get('page_id'))
            _, _, crawled_introductory, crawled_html, crawled_sentences = get_wiki_information(page.token)
            source_sentence = Sentence.objects.create(sentence_content=request.POST.get('source_sentence')
                                                      .split(' | دیکشنری‌مروبطه: ')[0].strip(), page=page)
            for claim in page.claims.all():
                claim.sentence = source_sentence
                claim.save()
            for sentence in page.sentences.filter(~Q(id=source_sentence.id)):
                sentence.delete()
            page.hyperlinks.clear()
            source_sentence_detected = False
            for sentence_text, hyperlinks in crawled_sentences.items():
                if sentence_text.strip() == request.POST.get('source_sentence').split(' | دیکشنری‌مروبطه: ')[0].strip():
                    source_sentence_detected = True
                    sentence = source_sentence
                else:
                    sentence = Sentence.objects.create(sentence_content=sentence_text, page=page)
                for hyperlink in hyperlinks:
                    hyperlink_token, hyperlink_title, hyperlink_first_paragraph = get_hyperlink_information(hyperlink)
                    hyperlink = Hyperlink.objects.filter(token=hyperlink_token)
                    if hyperlink.exists():
                        hyperlink = hyperlink.first()
                    else:
                        hyperlink = Hyperlink.objects.create(token=hyperlink_token, title=hyperlink_title,
                                                             first_paragraph=hyperlink_first_paragraph)
                    hyperlink.pages.add(page)
                    hyperlink.sentences.add(sentence)
                    hyperlink.save()
            if not source_sentence_detected:
                with open('source_sentences_not_detected.txt', 'a+', encoding='utf-8') as skipped_page_tokens_file:
                    skipped_page_tokens_file.write(page.token+'\n')
                raise ValueError('Source Sentence Not Detected!')
            page.page_content = crawled_introductory
            page.page_content_html = crawled_html
            page.save()
            with open('checked_page_tokens.txt', 'a+', encoding='utf-8') as checked_page_tokens_file:
                checked_page_tokens_file.write(page.token+'\n')
            return redirect(reverse('check_sentences'))
        elif action == 'Source Sentence Changed':
            page = Page.objects.get(id=request.POST.get('page_id'))
            with open('skipped_page_tokens.txt', 'a+', encoding='utf-8') as skipped_page_tokens_file:
                skipped_page_tokens_file.write(page.token+'\n')
            return redirect(reverse('check_sentences'))
        else:
            return redirect(reverse('index'))


class Wf2View(View):
    form_class = Wf2Form
    template_name = 'annotate-wf2.html'

    def get(self, request, *args, **kwargs):
        disable_elements = False
        skipped = False
        skip_reason = None
        if 'edit' in request.GET and 'claim_id' in request.GET \
                and 'user_id' in request.GET and eval(request.GET['edit']):
            edit = True
            claim = Claim.objects.get(id=request.GET['claim_id'])
            if request.user.id != int(request.GET['user_id']):
                disable_elements = True
        else:
            edit = False
            # # Double check 500 random labels. (start)
            # with open('random_claim_ids.txt', encoding='utf-8') as random_claim_ids_file:
            #     random_claim_ids = eval(random_claim_ids_file.read())
            #     for claim_id in random_claim_ids:
            #         if ClaimState.objects.filter(Q(user=request.user) & Q(claim_id=claim_id)
            #                                      & ~Q(state=0)).exists():
            #             continue
            #         claim = Claim.objects.get(id=claim_id)
            #         ClaimState.objects.get_or_create(user=request.user, claim=claim, state=0)
            #         break
            #     else:
            #         return redirect(reverse('index'))
            # # Double check 500 random labels. (end)
            # Normal mode (start)
            user_incomplete_claims = ClaimState.objects.filter(user=request.user, state=0)
            if user_incomplete_claims.exists():
                claim = user_incomplete_claims.first().claim
            else:
                # other_users_claims = ClaimState.objects.filter(~Q(user=request.user) & Q(state=2))
                # if other_users_claims.exists():
                #     claim = other_users_claims.first().claim
                #     ClaimState.objects.create(user=request.user, claim=claim, state=0)
                # else:
                unacceptable_claims = ClaimState.objects.all()   # state != assigned
                unacceptable_claims = [item.claim_id for item in unacceptable_claims]
                with open('skipped_page_tokens.txt', encoding='utf-8') as skipped_page_tokens_file:
                    skipped_page_tokens = [page_token.strip() for page_token in skipped_page_tokens_file.readlines()]
                claims = Claim.objects.filter(~Q(page__token__in=skipped_page_tokens) & ~Q(user=request.user)
                                              & ~Q(parent_claim=None) & ~Q(id__in=unacceptable_claims) &
                                              ~Q(claim_content__regex=r"\s*#\s*"))
                if claims.exists():
                    claim = claims.first()
                    ClaimState.objects.get_or_create(user=request.user, claim=claim, state=0)
                else:
                    return redirect(reverse('index'))
            # Normal mode (end)
        wf2_form = self.form_class(initial={'claim_id': claim.id})
        if edit:
            claim_state = ClaimState.objects.get(claim=claim, user_id=request.GET['user_id']).state
            if claim_state in [1, 2, 3, 4]:
                skipped = True
                skip_reason = CLAIM_STATES[claim_state][1]
            sentences = list(claim.page.sentences.all().values('id', 'sentence_content'))
            for i in range(len(sentences)):
                label = Label.objects.filter(claim=claim, sentence_id=sentences[i]['id'],
                                             user_id=request.GET['user_id'])
                if not label.exists():
                    sentences[i]['background_color'] = "#eeeeee"
                else:
                    if label.first().label:
                        sentences[i]['background_color'] = "#ff6666"
                    else:
                        sentences[i]['background_color'] = "#66ff66"
        else:
            unacceptable_sentences = Label.objects.filter(claim=claim, user=request.user)
            unacceptable_sentences = [item.sentence_id for item in unacceptable_sentences]
            sentences = list(claim.page.sentences.filter(~Q(id__in=unacceptable_sentences))
                             .values('id', 'sentence_content'))
            for i in range(len(sentences)):
                sentences[i]['background_color'] = "#eeeeee"
        context = {
            'edit': edit,
            'disable_elements': disable_elements,
            'skipped': skipped,
            'skip_reason': skip_reason,
            'claim': claim,
            'user_id': request.GET.get('user_id', None),
            'sentences': sentences,
            'form': wf2_form
        }
        return render(request, self.template_name, context)


class WF2ReviewView(View):
    form_class = WF2ReviewForm
    template_name = 'review-wf2.html'

    def get(self, request, *args, **kwargs):
        review_form = self.form_class()
        context = {
            'form': review_form,
        }
        return render(request, self.template_name, context)
