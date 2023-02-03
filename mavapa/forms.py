#!/usr/bin/env python
from wtforms import (BooleanField, Form, IntegerField, PasswordField,
                     StringField, SubmitField)
from wtforms.validators import Email, EqualTo, Required


class Login(Form):
    email = StringField('Email', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    remember = BooleanField('Remember Me', default=False)
    submit = SubmitField("Sign In")

    
class Profile(Form):
    email = StringField('Email', [Required(), Email()])

    
class AppForm(Form):
    name = StringField('Name', [Required()])
    desc = StringField('Description', [Required()])
    redirect_uri = StringField('redirect uri', [Required()])
    submit = SubmitField("Save")

    
class Reset(Form):
    email   = StringField('Email', [Required(), Email()])
    code    = StringField('Code')
    passwd  = PasswordField('Password',
                            [EqualTo('confirm',
                                     message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    check   = SubmitField("Next")
    submit  = SubmitField("Verify")
    change  = SubmitField("Send")
