# Generated by Django 3.0.8 on 2020-07-24 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_page_page_content_html'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='as_evidence',
            field=models.BooleanField(default=False),
        ),
    ]