from datetime import timedelta
from django.template.response import TemplateResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from wf1.forms import WF1ReviewForm, Wf1aForm, Wf1bForm
from wf1.models import Claim, Sentence
from wiki.models import Page, Hyperlink
import random
from django.views import View
from django.db import transaction


def tutorial(request):
    return TemplateResponse(request, 'tutorial.html')


class WF1ReviewView(View):
    form_class = WF1ReviewForm
    template_name = 'review-wf1.html'

    def get(self, request, *args, **kwargs):
        review_form = self.form_class()
        context = {
            'form': review_form,
        }
        return render(request, self.template_name, context)


class Wf1aView(View):
    form_class = Wf1aForm
    template_name = 'annotate-wf1a.html'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        disable_elements = False
        if 'edit' in request.GET and 'page_id' in request.GET\
                and eval(request.GET['edit']):
            edit = True
            page = Page.objects.get(id=request.GET['page_id'])
            if request.user != page.user:
                disable_elements = True
        else:
            edit = False
            pages = Page.objects.filter(useless=False, status=1, user=request.user, as_evidence=False)
            if pages.exists():
                page = pages.first()
            else:
                pages = Page.objects.filter(useless=False, status=2, user=request.user)
                if pages.exists():
                    sentence = pages.first().claims.first().sentence
                    return redirect(f'/wf1/wf1b/{sentence.id}/')
                else:
                    pages = Page.objects.filter(useless=False, status=0)
                    if not pages.exists():
                        return redirect(reverse('index'))
                    page = random.choice(pages)
                    page = Page.objects.select_for_update().filter(id=page.id).first()
                    page.status = 1
                    page.user = request.user
                    page.save()
        hyperlinks = Hyperlink.objects.filter(pages__in=[page])
        claims = '\n'.join([c.claim_content for c in page.claims.filter(parent_claim=None)])
        if page.claims.exists():
            source_sentence = page.claims.first().sentence
            wf1a_form = self.form_class(page_id=page.id, initial={'page_id': page.id, 'claims': claims,
                                                                  'source_sentence': source_sentence})
        else:
            wf1a_form = self.form_class(page_id=page.id, initial={'page_id': page.id, 'claims': claims})
        if disable_elements:
            for field_name in wf1a_form.fields:
                wf1a_form.fields[field_name].disabled = True
        else:
            wf1a_form.fields['source_sentence'].disabled = edit
        context = {
            'page': page,
            'edit': edit,
            'hyperlinks': hyperlinks,
            'form': wf1a_form
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if 'edit' in request.GET and eval(request.GET['edit']):
            edit = True
        else:
            edit = False
        action = request.POST.get('action')
        if action == 'home':
            return redirect(reverse('index'))
        else:
            page_id = request.POST.get('page_id')
            page = Page.objects.get(id=page_id)
            post = request.POST.copy()
            if action == 'useless':
                if page.status != 1 or page.user != request.user:
                    return redirect('/wf1/wf1a/')
                page.useless = True
                page.save()
                return redirect(reverse('wf1a'))
            elif action == 'submit':
                if 'source_sentence' not in post:
                    post['source_sentence'] = page.claims.first().sentence
                if page.status not in [1, 2, 3] or page.user != request.user:
                    return redirect('/wf1/wf1a/')
                wf1a_form = self.form_class(post, page_id=page_id)
                if wf1a_form.is_valid():
                    old_claims = page.claims.filter(parent_claim=None)
                    claim_contents = wf1a_form.cleaned_data['claims'].splitlines()
                    for claim in old_claims:
                        if claim.claim_content in claim_contents:
                            claim_contents.remove(claim.claim_content)
                        else:
                            claim.delete()
                    for claim_content in claim_contents:
                        Claim.objects.create(claim_content=claim_content, page=page,
                                             sentence=wf1a_form.cleaned_data['source_sentence'],
                                             user=request.user)
                    if len(claim_contents) > 0:
                        page.status = 2
                        page.save()
                        return redirect(f'/wf1/wf1b/{wf1a_form.cleaned_data["source_sentence"].id}/?edit={edit}')
                    else:
                        return redirect(reverse('wf1a'))
                else:
                    page = Page.objects.get(id=page_id)
                    hyperlinks = Hyperlink.objects.filter(pages__in=[page])
                    context = {
                        'page': page,
                        'hyperlinks': hyperlinks,
                        'form': wf1a_form
                    }
                    return render(request, self.template_name, context)


class Wf1bView(View):
    form_class = Wf1bForm
    template_name = 'annotate-wf1b.html'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        if 'edit' in request.GET and eval(request.GET['edit']):
            edit = True
        else:
            edit = False
        source_sentence = Sentence.objects.get(id=kwargs['source_sentence_id'])
        page = source_sentence.page
        if not edit and (page.status not in [2, 3] or page.user != request.user):
            return redirect('/wf1/wf1a/')
        if edit and page.user != request.user:
            disable_elements = True
        else:
            disable_elements = False
        context_before, context_after = page.page_content.split(source_sentence.sentence_content.strip())
        hyperlinks = Hyperlink.objects.filter(sentences__in=[source_sentence])
        claims = source_sentence.claims.filter(parent_claim=None)
        forms = []
        for claim in claims.all():
            rephrase = '\n'.join([c.claim_content for c in Claim.objects.filter(parent_claim=claim, mutation_type=0)])
            negate = '\n'.join([c.claim_content for c in Claim.objects.filter(parent_claim=claim, mutation_type=1)])
            similar = '\n'.join([c.claim_content for c in Claim.objects.filter(parent_claim=claim, mutation_type=2)])
            dissimilar = '\n'.join([c.claim_content for c in Claim.objects.filter(parent_claim=claim, mutation_type=3)])
            specific = '\n'.join([c.claim_content for c in Claim.objects.filter(parent_claim=claim, mutation_type=4)])
            general = '\n'.join([c.claim_content for c in Claim.objects.filter(parent_claim=claim, mutation_type=5)])
            form = self.form_class(prefix=claim.id,
                                   initial={'source_claim_id': claim.id,
                                            'source_claim_content': claim.claim_content,
                                            'rephrase': rephrase, 'negate': negate,
                                            'similar': similar, 'dissimilar': dissimilar,
                                            'specific': specific, 'general': general})
            if disable_elements:
                for field_name in form.fields:
                    form.fields[field_name].disabled = True
            forms.append(form)
        context = {
            'edit': edit,
            'page': page,
            'source_sentence_id': kwargs['source_sentence_id'],
            'context_before': context_before,
            'context_after': context_after,
            'source_sentence_content': source_sentence.sentence_content,
            'hyperlinks': hyperlinks,
            'forms': forms
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if 'edit' in request.GET and eval(request.GET['edit']):
            edit = True
        else:
            edit = False
        source_sentence = Sentence.objects.get(id=kwargs['source_sentence_id'])
        claims = source_sentence.claims.filter(parent_claim=None)
        page = source_sentence.page
        if page.status not in [2, 3] or page.user != request.user:
            return redirect('/wf1/wf1a/')
        forms = []
        is_valid = True
        for i in range(len(claims)):
            forms.append(self.form_class(request.POST, prefix=claims[i].id))
            if not forms[i].is_valid():
                is_valid = False
        if not is_valid:
            context_before, context_after = page.page_content.split(source_sentence.sentence_content)
            hyperlinks = Hyperlink.objects.filter(pages__in=[page])
            context = {
                'page_title': page.title,
                'source_sentence_id': kwargs['source_sentence_id'],
                'context_before': context_before,
                'context_after': context_after,
                'source_sentence_content': source_sentence.sentence_content,
                'hyperlinks': hyperlinks,
                'error_detected': True,
                'forms': forms
            }
            return render(request, self.template_name, context)

        total_claims_done = 0
        for form in forms:
            Claim.objects.filter(parent_claim_id=form.cleaned_data['source_claim_id']).delete()
            rephrases = form.cleaned_data['rephrase'].splitlines()
            for rephrase in rephrases:
                Claim.objects.create(claim_content=rephrase, page=page, mutation_type=0,
                                     parent_claim_id=form.cleaned_data['source_claim_id'],
                                     sentence=source_sentence, user=request.user)
            total_claims_done += len(rephrases)
            negates = form.cleaned_data['negate'].splitlines()
            for negate in negates:
                Claim.objects.create(claim_content=negate, page=page, mutation_type=1,
                                     parent_claim_id=form.cleaned_data['source_claim_id'],
                                     sentence=source_sentence, user=request.user)
            total_claims_done += len(negates)
            similars = form.cleaned_data['similar'].splitlines()
            for similar in similars:
                Claim.objects.create(claim_content=similar, page=page, mutation_type=2,
                                     parent_claim_id=form.cleaned_data['source_claim_id'],
                                     sentence=source_sentence, user=request.user)
            total_claims_done += len(similars)
            dissimilars = form.cleaned_data['dissimilar'].splitlines()
            for dissimilar in dissimilars:
                Claim.objects.create(claim_content=dissimilar, page=page, mutation_type=3,
                                     parent_claim_id=form.cleaned_data['source_claim_id'],
                                     sentence=source_sentence, user=request.user)
            total_claims_done += len(dissimilars)
            specifics = form.cleaned_data['specific'].splitlines()
            for specific in specifics:
                Claim.objects.create(claim_content=specific, page=page, mutation_type=4,
                                     parent_claim_id=form.cleaned_data['source_claim_id'],
                                     sentence=source_sentence, user=request.user)
            total_claims_done += len(specifics)
            generals = form.cleaned_data['general'].splitlines()
            for general in generals:
                Claim.objects.create(claim_content=general, page=page, mutation_type=5,
                                     parent_claim_id=form.cleaned_data['source_claim_id'],
                                     sentence=source_sentence, user=request.user)
            total_claims_done += len(generals)
        page.status = 3
        page.save()
        request.user.page_claim_count = request.user.pages.filter(status=3).count()
        request.user.total_claim_count = request.user.claims.filter(~Q(claim_content__regex=r"\s*#\s*")).count()
        request.user.save()
        return redirect(reverse('wf1a'))
