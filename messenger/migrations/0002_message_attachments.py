from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("messenger", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="text",
            field=models.TextField(blank=True, max_length=5000),
        ),
        migrations.AddField(
            model_name="message",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="chat_files/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="message",
            name="original_filename",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="message",
            name="file_size",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
