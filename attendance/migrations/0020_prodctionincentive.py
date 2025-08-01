# Generated by Django 5.2 on 2025-07-26 06:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0019_remove_historicalnotrunningday_history_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProdctionIncentive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date_issued', models.DateField()),
                ('reason', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prodction_incentive', to='attendance.employee')),
            ],
            options={
                'ordering': ['-date_issued'],
            },
        ),
    ]
