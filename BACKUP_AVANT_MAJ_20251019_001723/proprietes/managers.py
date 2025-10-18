from django.db import models

class NonDeletedQuerySet(models.QuerySet):
    def not_deleted(self):
        return self.filter(is_deleted=False)

class NonDeletedManager(models.Manager):
    def get_queryset(self):
        return NonDeletedQuerySet(self.model, using=self._db).not_deleted() 