# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cdr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('calldate', models.DateTimeField(blank=True)),
                ('clid', models.CharField(max_length=80, blank=True)),
                ('src', models.CharField(max_length=80, blank=True)),
                ('dst', models.CharField(max_length=80, blank=True)),
                ('dcontext', models.CharField(max_length=80, blank=True)),
                ('channel', models.CharField(max_length=80, blank=True)),
                ('dstchannel', models.CharField(max_length=80, blank=True)),
                ('lastapp', models.CharField(max_length=80, blank=True)),
                ('lastdata', models.CharField(max_length=80, blank=True)),
                ('duration', models.IntegerField(blank=True)),
                ('billsec', models.IntegerField(blank=True)),
                ('disposition', models.CharField(max_length=45, blank=True)),
                ('amaflags', models.IntegerField(blank=True)),
                ('accountcode', models.CharField(max_length=20, blank=True)),
                ('uniqueid', models.CharField(max_length=32, blank=True)),
                ('userfield', models.CharField(max_length=255, blank=True)),
                ('is_new', models.BooleanField(default=False))
            ],
            options={
                'db_table': 'cdr',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Cel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('eventtype', models.CharField(max_length=30)),
                ('eventtime', models.DateTimeField()),
                ('cid_name', models.CharField(max_length=80)),
                ('cid_num', models.CharField(max_length=80)),
                ('cid_ani', models.CharField(max_length=80)),
                ('cid_rdnis', models.CharField(max_length=80)),
                ('cid_dnid', models.CharField(max_length=80)),
                ('exten', models.CharField(max_length=80)),
                ('context', models.CharField(max_length=80)),
                ('channame', models.CharField(max_length=80)),
                ('src', models.CharField(max_length=80)),
                ('dst', models.CharField(max_length=80)),
                ('channel', models.CharField(max_length=80)),
                ('dstchannel', models.CharField(max_length=80)),
                ('appname', models.CharField(max_length=80)),
                ('appdata', models.CharField(max_length=80)),
                ('amaflags', models.IntegerField()),
                ('accountcode', models.CharField(max_length=20)),
                ('uniqueid', models.CharField(max_length=32)),
                ('linkedid', models.CharField(max_length=32)),
                ('peer', models.CharField(max_length=80)),
                ('userdeftype', models.CharField(max_length=255)),
                ('eventextra', models.CharField(max_length=255)),
                ('userfield', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'cel',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Numbers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('abc', models.IntegerField()),
                ('of', models.IntegerField()),
                ('to', models.IntegerField()),
                ('capacity', models.IntegerField()),
                ('operator', models.CharField(max_length=255)),
                ('region', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'numbers',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='QueueLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.CharField(max_length=32, null=True, blank=True)),
                ('callid', models.CharField(max_length=64, null=True, blank=True)),
                ('queuename', models.CharField(max_length=64, null=True, blank=True)),
                ('agent', models.CharField(max_length=64, null=True, blank=True)),
                ('event', models.CharField(max_length=32, null=True, blank=True)),
                ('data', models.CharField(max_length=64, null=True, blank=True)),
                ('data1', models.CharField(max_length=64, null=True, blank=True)),
                ('data2', models.CharField(max_length=64, null=True, blank=True)),
                ('data3', models.CharField(max_length=64, null=True, blank=True)),
                ('data4', models.CharField(max_length=64, null=True, blank=True)),
                ('data5', models.CharField(max_length=64, null=True, blank=True)),
            ],
            options={
                'db_table': 'queue_log',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'department',
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('department', models.ForeignKey(blank=True, to='asterisk.Department', null=True)),
            ],
            options={
                'db_table': 'employee',
            },
        ),
        migrations.CreateModel(
            name='ExternalPhoneNumber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone_number', models.CharField(max_length=20)),
                ('note', models.CharField(max_length=500, null=True, blank=True)),
            ],
            options={
                'db_table': 'external_phone_number',
            },
        ),
        migrations.CreateModel(
            name='InternalPhoneNumber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone_number', models.CharField(max_length=20)),
                ('department', models.ForeignKey(blank=True, to='asterisk.Department', null=True)),
                ('employee', models.ForeignKey(blank=True, to='asterisk.Employee', null=True)),
            ],
            options={
                'db_table': 'internal_phone_number',
            },
        ),
        migrations.CreateModel(
            name='Websites',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'db_table': 'websites',
            },
        ),
        migrations.AddField(
            model_name='externalphonenumber',
            name='website',
            field=models.ForeignKey(blank=True, to='asterisk.Websites', null=True),
        ),
    ]
