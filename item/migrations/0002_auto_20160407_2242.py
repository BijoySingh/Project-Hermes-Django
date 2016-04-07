# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-07 17:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reactable',
            name='experience',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='reaction',
            name='reactable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='item.Reactable'),
        ),
        migrations.AlterField(
            model_name='reaction',
            name='reaction',
            field=models.IntegerField(choices=[(0, 'None'), (1, 'Upvote'), (2, 'Downvote'), (3, 'Flag')], default=0),
        ),
    ]
