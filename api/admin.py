from django.contrib import admin
from api import models 

admin.site.register(models.Teacher)
admin.site.register(models.Category)
admin.site.register(models.Course)
admin.site.register(models.Variant)
admin.site.register(models.VariantItem)
admin.site.register(models.Question_Answer)
admin.site.register(models.Question_Answer_Message)
admin.site.register(models.Cart)
admin.site.register(models.CartOrder)
admin.site.register(models.CartOrderItem)
admin.site.register(models.Certificate)
admin.site.register(models.CompletedLesson)
admin.site.register(models.EnrolledCourse)
admin.site.register(models.Note)
admin.site.register(models.Review)
admin.site.register(models.Notification)
admin.site.register(models.Coupon)
admin.site.register(models.Wishlist)
admin.site.register(models.Country)

# Group model registration
@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name']

# Quizzes model registration
@admin.register(models.Quizzes)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'group']

# Questions model registration
@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'quiz', 'date_updated']

# Answers model registration
@admin.register(models.Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['answer_text', 'is_right', 'question']

@admin.register(models.WritingAnswer)
class WritingAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'user', 'submitted_at']
    search_fields = ['user__email', 'question__title']
    list_filter = ['submitted_at']