# Generated by Django 3.0.6 on 2020-07-14 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0002_auto_20200528_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='page_content_html',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
