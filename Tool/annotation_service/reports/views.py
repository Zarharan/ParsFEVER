from django.shortcuts import render
from accounts.models import User
from wf1.models import Claim
from django.db.models import Q

from wf2.models import Label, ClaimState


def statistics(request):
    context = {'header': ['First Name', 'Last Name', '# Pages Completed',
                          '# Main Claims Generated', '# Mutation Generated',
                          '# Label Generated', '# Claims Done',
                          'WF1 Total', 'WF2 Total', 'Total'],
               'rows': []}
    users = User.objects.filter()
    total_pages_count = 0
    total_main_claims_count = 0
    total_mutations_count = 0
    total_label_count = 0
    total_annotation_count = 0
    for user in users:
        main_claims_count = Claim.objects.filter(user=user, parent_claim=None).count()
        mutations_count = Claim.objects.filter(Q(user=user) & ~Q(parent_claim=None) &
                                               ~Q(claim_content__regex=r"\s*#\s*")).count()
        label_count = Label.objects.filter(user=user).count()
        annotation_count = ClaimState.objects.filter(Q(user=user) & ~Q(state=0)).count()
        wf1_total_count = main_claims_count + mutations_count
        wf2_total_count = label_count + annotation_count
        total_pages_count += user.page_claim_count
        total_main_claims_count += main_claims_count
        total_mutations_count += mutations_count
        total_label_count += label_count
        total_annotation_count += annotation_count
        context['rows'].append({'first_name': user.first_name, 'last_name': user.last_name,
                                'pages_count': user.page_claim_count,
                                'main_claims_count': main_claims_count,
                                'mutations_count': mutations_count,
                                'label_count': label_count,
                                'annotation_count': annotation_count,
                                'wf1_total_count': wf1_total_count,
                                'wf2_total_count': wf2_total_count,
                                'total_count': wf1_total_count+wf2_total_count})
    context['total_pages_count'] = total_pages_count
    context['total_main_claims_count'] = total_main_claims_count
    context['total_mutations_count'] = total_mutations_count
    context['total_label_count'] = total_label_count
    context['total_annotation_count'] = total_annotation_count
    context['total_wf1_count'] = total_main_claims_count + total_mutations_count
    context['total_wf2_count'] = total_label_count + total_annotation_count
    context['total_count'] = context['total_wf1_count'] + context['total_wf2_count']
    return render(request, 'statistics.html', context)
