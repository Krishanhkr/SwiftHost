#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zero Trust Security Module
-------------------------
Provides Zero Trust Network Access (ZTNA) capabilities for the honeypot.
"""

from .zero_trust import ztna_manager, ztna_login_required, ztna_role_required
from .auth_routes import auth_bp

__all__ = ['ztna_manager', 'ztna_login_required', 'ztna_role_required', 'auth_bp'] 