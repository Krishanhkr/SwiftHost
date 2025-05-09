#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deception Technologies Module
-----------------------------
This module provides fake microservices that mimic Redis, MySQL, and AWS S3 APIs
to track attacker behavior and inject tracking payloads.
"""

from .api_honeypot import deception_bp
from .analytics import DeceptionAnalytics

__all__ = ['deception_bp', 'DeceptionAnalytics'] 