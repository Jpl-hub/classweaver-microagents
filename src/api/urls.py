from django.urls import path

from . import views


urlpatterns = [
    path("prestudy/from-text/", views.PrestudyFromTextView.as_view(), name="prestudy-from-text"),
    path("prestudy/from-ppt/", views.PrestudyFromPptView.as_view(), name="prestudy-from-ppt"),
    path("prestudy/<int:pk>/", views.PrestudyDetailView.as_view(), name="prestudy-detail"),
    path("quiz/start/", views.QuizStartView.as_view(), name="quiz-start"),
    path("quiz/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
    path("kb/upload/", views.KnowledgeUploadView.as_view(), name="kb-upload"),
    path("kb/search/", views.KnowledgeSearchView.as_view(), name="kb-search"),
]
