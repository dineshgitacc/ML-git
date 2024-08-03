"""classification URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from training.views import LoginView,FileUploadView,AnalysisFileUploadView,FileDetailsView,ClassificationsView,TrainingNamesView,FileUploadDraftView,FileDatasetList, AlgorithmSelectView, AlgorithmDetailView, TrainingNamesAvailableView, ModelDetailsView, UserRegistrationView, UserListView, AnalysisTextList, AnalysisClassifyCallBack, UpdateAnalysisClassification, UpateAnalysisIntent, UpdateAnalysisEntities, ReTraining
from inference.views import InferenceUploadView,InferenceTextView,InferenceListView,InferenceDetailsView
from dataset.views import DatasetFolderView,DatasetUploadView,DatasetListView,DatasetDetailsView,DataFileDetailsView,DatasetSaveView
from django.conf import settings
from django.conf.urls.static import static
from analysis_request.views import AnalysisRequestView, AddSolutionAnalysisRequest, UpdateSolutionAnalysisRequest, DeleteSolutionAnalysisRequest, SolutionAnalysisRequestList, SolutionAnalysisMappingDataList,SupervisedModelTraining

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('accounts/register/', UserRegistrationView.as_view()),
    path('user/list/', UserListView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('training/upload/', FileUploadView.as_view()),
    path('analysis/training/upload/', AnalysisFileUploadView.as_view()),
    path('training/details/', FileDetailsView.as_view()),
    path('classification/list/', ClassificationsView.as_view()),
    path('training_name/list/', TrainingNamesView.as_view()),
    path('training_name/available/', TrainingNamesAvailableView.as_view()),
    path('training/upload/draft/', FileUploadDraftView.as_view()),
    path('training/dataset/list/', FileDatasetList.as_view()),
    path('algorithm/select/', AlgorithmSelectView.as_view()),
    path('algorithm/details/', AlgorithmDetailView.as_view()),
    path('inference/list/', InferenceListView.as_view()),
    path('inference/add/', InferenceTextView.as_view()),
    path('inference/details/', InferenceDetailsView.as_view()),
    path('model/details/', ModelDetailsView.as_view()),
    path('folder/check/', DatasetFolderView.as_view()),
    path('dataset/upload/', DatasetUploadView.as_view()),
    path('dataset/list/', DatasetListView.as_view()),
    path('dataset/details/', DatasetDetailsView.as_view()),
    path('file/details/', DataFileDetailsView.as_view()),
    path('dataset/save/', DatasetSaveView.as_view()),
    path('analysis/dataset/list/', AnalysisTextList.as_view()),

    
    # Make call from ETL ( Airflow )
    path('analysis/request/create/', AnalysisRequestView.as_view({'post': 'create'})),

    path('classifycallback/', AnalysisClassifyCallBack.as_view()),
    path('textmaster/classification/', UpdateAnalysisClassification.as_view()),
    path('textmaster/intent/', UpateAnalysisIntent.as_view()),
    path('textmaster/entities/', UpdateAnalysisEntities.as_view()),
    path('retraining/details/', ReTraining.as_view()),

    path('analysis/cluster/intent_entity/callback/', AnalysisRequestView.as_view({'post': 'intent_entity'})),
    path('analysis/cluster/sentiment_analysis/callback/', AnalysisRequestView.as_view({'post': 'sentiment_analysis'})),
    path('analysis/cluster/predictive_analysis/callback/', AnalysisRequestView.as_view({'post': 'predictive_analysis'})),
    path('analysis/cluster/classification/callback/', AnalysisRequestView.as_view({'post': 'classification_callback'})),
    path('analysis/bert/intent/callback/', AnalysisRequestView.as_view({'post': 'bert_intent_callback'})),

    path('analysis/hierarchical_clustering/callback/', AnalysisRequestView.as_view({'post': 'hierarchical_clustering_callback'})),
    path('analysis/solution/add', AddSolutionAnalysisRequest.as_view()),
    path('analysis/solution/update', UpdateSolutionAnalysisRequest.as_view()),
    path('analysis/solution/delete', DeleteSolutionAnalysisRequest.as_view()),
    path('analysis/solution/list', SolutionAnalysisRequestList.as_view()),
    path('analysis/solution/mapping/list', SolutionAnalysisMappingDataList.as_view()),

    path('training/supervised', SupervisedModelTraining.as_view(),name='SupervisedModelTraining'),

]


if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
