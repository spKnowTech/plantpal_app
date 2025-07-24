from fastapi import Depends, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/dashboard", tags=['Dashboard'])
templates = Jinja2Templates(directory='templates')

@router.get('/')
async def dashboard(request: Request):
    return templates.TemplateResponse('dashboard_page.html', context={'request': request})