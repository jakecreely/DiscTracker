from django.shortcuts import redirect
from django.views.generic.base import TemplateView
import logging

logger = logging.getLogger(__name__)


def home(request):
    if request.user.is_authenticated:
        logger.info(
            f"Authenticated user '{request.user.username}' accessed home and was redirected."
        )
        return redirect("items:index")
    else:
        logger.info("Unauthenticated user accessed home page.")
        return TemplateView.as_view(template_name="index.html")(request)
