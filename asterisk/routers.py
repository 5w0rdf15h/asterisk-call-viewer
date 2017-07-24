# -*- coding: utf-8 -*-


class DbRouter(object):

    external_db_models = ['cdr', 'numbers']

    def db_for_read(self, model, **hints):
        """
        Use original asterisk Db tables for read
        """
        if model._meta.model_name.lower() in self.external_db_models:
            return 'asterisk'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name.lower() in self.external_db_models:
            return 'asterisk'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label == 'asterisk':
            return db == 'asterisk'
        return True
