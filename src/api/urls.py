from django.urls import path

from . import views


urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", views.CurrentUserView.as_view(), name="auth-me"),
    path("auth/csrf/", views.CsrfTokenView.as_view(), name="auth-csrf"),
    path("prestudy/from-text/", views.PrestudyFromTextView.as_view(), name="prestudy-from-text"),
    path("prestudy/from-ppt/", views.PrestudyFromPptView.as_view(), name="prestudy-from-ppt"),
    path("prestudy/<int:pk>/", views.PrestudyDetailView.as_view(), name="prestudy-detail"),
    path("jobs/<int:pk>/", views.PrestudyJobStatusView.as_view(), name="prestudy-job-status"),
    path("quiz/start/", views.QuizStartView.as_view(), name="quiz-start"),
    path("quiz/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
    path("kb/upload/", views.KnowledgeUploadView.as_view(), name="kb-upload"),
    path("kb/search/", views.KnowledgeSearchView.as_view(), name="kb-search"),
    path("kb/qa/", views.KnowledgeQaView.as_view(), name="kb-qa"),
    path("kb/documents/", views.KnowledgeDocumentListView.as_view(), name="kb-documents"),
    path("kb/documents/<str:doc_id>/", views.KnowledgeDocumentDetailView.as_view(), name="kb-documents-detail"),
    path("kb/bases/", views.KnowledgeBaseListCreateView.as_view(), name="kb-bases"),
    path("kb/bases/<int:pk>/", views.KnowledgeBaseDetailView.as_view(), name="kb-bases-detail"),
    path("lesson/<int:pk>/timeline/", views.LessonTimelineView.as_view(), name="lesson-timeline"),
    path("lesson/<int:pk>/events/", views.LessonEventCreateView.as_view(), name="lesson-event-create"),
    path("recommendations/", views.RecommendationTriggerView.as_view(), name="recommendations"),
]
