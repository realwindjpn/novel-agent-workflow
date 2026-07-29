"""Helper scripts and launchers for the novel-workflow project.

This package exposes the long-lived launcher / bridge utilities that the
local SPA, the desktop launcher, and the test suite all share. Keeping
them under ``scripts/`` (alongside the standalone CLI helpers) lets
tests import them via ``scripts.<module>`` while still letting the
modules be executed directly with ``python -m``.
"""
