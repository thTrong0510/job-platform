from app.repositories.user_repository import UserRepository

from common.CloudinaryUtil import CloudinaryUtil


class UserService:
    def save_user(user):
        return UserRepository.save(user)

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    @staticmethod
    def update_avatar(user_id, file):

        if not UserService._allowed_file(file.filename):
            raise Exception("Invalid file type. Only images allowed.")

        # Upload to Cloudinary
        avatar_url = CloudinaryUtil.upload_image(file)

        if not avatar_url:
            raise Exception("Upload failed")

        # Update DB
        UserRepository.update_avatar(user_id, avatar_url)

    @staticmethod
    def _allowed_file(filename):
        return (
            "." in filename and
            filename.rsplit(".", 1)[1].lower()
            in UserService.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def get_user_by_id(user_id):
        return UserRepository.find_by_id(user_id)