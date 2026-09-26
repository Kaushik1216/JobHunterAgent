# MCP Server Component Developer Documentation

## Overview
The `mcp_server` module implements a Model Context Protocol (MCP) server, allowing external AI agents or tools to interact with the Job Agent's functionality and database.

## Responsibilities
- Provide an MCP-compliant server implementation.
- Expose system capabilities (like searching jobs, triggering runs, or querying the database) as MCP tools.
- Manage connections and request routing from MCP clients.

## Key Files & Modules
- `server.py`: The main entry point for the MCP server, defining the server lifecycle, protocol handling, and initialization.
- `tools/`: A directory containing the implementations of individual MCP tools exposed by the server.

## Architecture & Interactions
- Acts as an alternative entry point to the system, running independently or alongside the dashboard.
- Interacts with `core`, `storage`, and `dashboard` components to expose their functionality over MCP.
