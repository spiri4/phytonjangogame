from django.db import models


class Winner(models.Model):
    """Запись о победителе: имя, дата победы, кол-во рядов грида."""
    winner_name = models.CharField('Имя победителя', max_length=200)
    victory_date = models.DateTimeField('Дата победы', auto_now_add=True)
    row_count = models.PositiveIntegerField('Кол-во рядов грида')

    class Meta:
        ordering = ['row_count', 'victory_date']
        verbose_name = 'Победитель'
        verbose_name_plural = 'Победители'

    def __str__(self):
        return f'{self.winner_name} — {self.row_count} рядов ({self.victory_date})'
