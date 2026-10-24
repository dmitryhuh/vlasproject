

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('made_app', '0006_profile_birthday'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostImage',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    ),
                ),
                (
                    'image',
                    models.ImageField(upload_to='posts/'),
                ),
                (
                    'post',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='images',
                        to='made_app.post',
                    ),
                ),
            ],
        ),
    ]
