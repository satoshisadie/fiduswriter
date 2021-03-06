#
# This file is part of Fidus Writer <http://www.fiduswriter.org>
#
# Copyright (C) 2013 Takuto Kojima, Johannes Wilm
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from django.db import models
from django.contrib.auth.models import User

from django.db import IntegrityError

ALLOWED_FILETYPES = ['image/jpeg','image/png','image/svg+xml']
ALLOWED_EXTENSIONS = ['jpeg','jpg','png','svg']

import uuid
def get_file_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    if not ext in ALLOWED_EXTENSIONS:
        raise IntegrityError
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('images', filename)

class Image(models.Model):
    title = models.CharField(max_length=128)
    uploader = models.ForeignKey(User,related_name='uploader')
    added = models.DateTimeField(auto_now_add=True)
    image = models.FileField(upload_to=get_file_path)
    thumbnail = models.ImageField(upload_to='image_thumbnails',max_length=500,blank=True,null=True)
    image_cat = models.CharField(max_length=255, default='')
    file_type = models.CharField(max_length=20,blank=True,null=True)
    height = models.IntegerField(blank=True,null=True)
    width = models.IntegerField(blank=True,null=True)
    checksum = models.BigIntegerField(max_length=50, default=0)
    
    
    def __unicode__(self):
        return self.title
    
    def create_checksum(self):
        if self.checksum == 0:
            from time import time
            if hasattr(self.image.file, 'size'):
                self.checksum = int(str(self.image.file.size) + str(time()).split('.')[0])
            else:
                self.checksum = time()
    
    def check_filetype(self):
        if not self.image:
            return
        if not hasattr(self.image.file, 'content_type'):
            return
        
        if not self.image.file.content_type in ALLOWED_FILETYPES:
            raise IntegrityError  
    
    def create_thumbnail(self):
        # original code for this method came from
        # http://snipt.net/danfreak/generate-thumbnails-in-django-with-pil/

        # If there is no image associated with this.
        # do not create thumbnail
        if not self.image:
            return
        if not hasattr(self.image.file, 'content_type'):
           return

        from PIL import Image as PilImage
        from cStringIO import StringIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        import os

        # Set our max thumbnail size in a tuple (max width, max height)
        #THUMBNAIL_SIZE = (170,200)

        DJANGO_TYPE = self.image.file.content_type

        if DJANGO_TYPE == 'image/jpeg':
            PIL_TYPE = 'jpeg'
            FILE_EXTENSION = 'jpg'
            self.file_type = DJANGO_TYPE
        elif DJANGO_TYPE == 'image/png':
            PIL_TYPE = 'png'
            FILE_EXTENSION = 'png'
            self.file_type = DJANGO_TYPE
        else:
            self.file_type = DJANGO_TYPE
            return
        
        # Open original photo which we want to thumbnail using PIL's Image
        image = PilImage.open(StringIO(self.image.read()))

        self.width, self.height = image.size
        
        #cropping the thumbnail to exactly 60 x 60 px
        src_width, src_height = image.size
        dst_width = dst_height = 60
        
        if src_width < src_height:
            crop_width = crop_height = src_width
            x_offset = 0
            y_offset = int(float(src_height - crop_height) / 2)
        else:
            crop_width = crop_height = src_height
            x_offset = int(float(src_width - crop_width) / 2)
            y_offset = 0
            
        image = image.crop((x_offset, y_offset, x_offset+int(crop_width), y_offset+int(crop_height)))
        
        # Convert to RGB if necessary
        # Thanks to Limodou on DjangoSnippets.org
        # http://www.djangosnippets.org/snippets/20/
        #
        # I commented this part since it messes up my png files
        #
        #if image.mode not in ('L', 'RGB'):
        #    image = image.convert('RGB')

        # We use our PIL Image object to create the thumbnail, which already
        # has a thumbnail() convenience method that contrains proportions.
        # Additionally, we use Image.ANTIALIAS to make the image look better.
        # Without antialiasing the image pattern artifacts may result.
        image.thumbnail((dst_width, dst_height), PilImage.ANTIALIAS)

        # Save the thumbnail
        temp_handle = StringIO()
        image.save(temp_handle, PIL_TYPE)
        temp_handle.seek(0)

        # Save image to a SimpleUploadedFile which can be saved into
        # ImageField
        suf = SimpleUploadedFile(os.path.split(self.image.name)[-1], temp_handle.read(), content_type=DJANGO_TYPE)
        # Save SimpleUploadedFile into image field
        self.thumbnail.save('%s_thumbnail.%s'%(os.path.splitext(suf.name)[0],FILE_EXTENSION), suf, save=False)
 
 
 
    def save(self):
        # create a thumbnail
        self.create_checksum()
        self.check_filetype()
        self.create_thumbnail()
 
        super(Image, self).save()
    
    
#category
class ImageCategory(models.Model):
    category_title = models.CharField(max_length=100)
    category_owner = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.category_title    
    
    class Meta:
        verbose_name_plural = 'Image categories'