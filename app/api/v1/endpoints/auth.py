from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.post("/signup/user")
async def user_signup():
    try:
        return "hi"
    except Exception as e :
        raise HTTPException(
            status_code=500,
            detail={"success":False,"msg":"Calendar generation failed"}
        )


@router.get("/me")
def read_current_user(user=Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email")
    }
