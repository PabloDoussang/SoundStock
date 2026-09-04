from types import SimpleNamespace
from .store import read, MockUser

class MockUserMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        request.user=SimpleNamespace(is_authenticated=False,is_superuser=False)
        uid=request.session.get('u1_user')
        if uid:
            row=next((u for u in read()['users'] if u['id']==uid and u['is_active']),None)
            if row and row['session_version']==request.session.get('u1_version'):
                request.user=MockUser(**row)
            else: request.session.flush()
        return self.get_response(request)

def user_context(request):
    return {'user':request.user,'runtime_label':'Prototipo U1 · JSON'}
