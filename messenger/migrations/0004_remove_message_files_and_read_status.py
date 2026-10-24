from django.db import migrations, models


def remove_attachments(apps, schema_editor):
    Message = apps.get_model("messenger", "Message")
    database = schema_editor.connection.alias
    messages = Message.objects.using(database).exclude(file="").exclude(file__isnull=True)
    empty_message_ids = []

    for message in messages.iterator():
        try:
            message.file.storage.delete(message.file.name)
        except (OSError, TypeError, ValueError):
            pass
        if not message.text.strip():
            empty_message_ids.append(message.pk)

    Message.objects.using(database).filter(pk__in=empty_message_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("messenger", "0003_repair_attachment_columns"),
    ]

    operations = [
        migrations.RunPython(remove_attachments, migrations.RunPython.noop),
        migrations.RemoveField(model_name="message", name="file"),
        migrations.RemoveField(model_name="message", name="original_filename"),
        migrations.RemoveField(model_name="message", name="file_size"),
        migrations.RemoveField(model_name="message", name="is_read"),
        migrations.AlterField(
            model_name="message",
            name="text",
            field=models.TextField(max_length=5000),
        ),
    ]
