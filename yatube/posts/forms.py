from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма для публикации постов."""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Поле, обязательное для заполнения!')
        return data


class CommentForm(forms.ModelForm):
    """Форма для добавления комментария."""

    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Поле, обязательное для заполнения!')
        return data
