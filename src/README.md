# Slalom Capabilities Management API

<p align="center">
  <img src="./.images/byte-teacher.png" alt="Byte Teacher" width="200" />
</p>

A FastAPI application that enables Slalom consultants to register their capabilities and manage consulting expertise across the organization.

## Features

- View all available consulting capabilities
- Register consultant expertise and availability
- Track skill levels and certifications
- Restrict consultant removal to authenticated practice leads
- Scope practice leads to their configured practice areas
- Record authentication and consultant-removal audit events

## Getting Started

1. Install the dependencies:

   ```bash
   pip install -r ../requirements.txt
   ```

2. Generate a password hash for the configured Technology practice lead:

   ```bash
   export TECHNOLOGY_LEAD_PASSWORD_HASH="$(python -c 'from getpass import getpass; from src.app import hash_password; print(hash_password(getpass("Password: ")))')"
   ```

   Practice-lead accounts and their authorized practice areas are defined in
   `practice_leads.json`. Password hashes are supplied through environment
   variables so credentials are never committed to source control.

3. Run the application from the repository root:

   ```bash
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc
   - Capabilities Dashboard: http://localhost:8000/

5. Run the tests:

   ```bash
   python -m pytest -q
   ```

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/capabilities`                                                   | Get all capabilities with details and current consultant assignments |
| POST   | `/auth/login`                                                      | Create an HttpOnly practice-lead session                              |
| GET    | `/auth/session`                                                    | Get the current authentication state                                  |
| POST   | `/auth/logout`                                                     | Revoke the current session                                             |
| POST   | `/capabilities/{capability_name}/register?email=consultant@slalom.com` | Register consultant for a capability                     |
| DELETE | `/capabilities/{capability_name}/unregister?email=consultant@slalom.com` | Unregister a consultant as an authorized practice lead |

## Data Model

The application uses a consulting-focused data model:

1. **Capabilities** - Uses capability name as identifier:
   - Description of the consulting capability
   - Skill levels (Emerging, Proficient, Advanced, Expert)
   - Practice area (Strategy, Technology, Operations)
   - Industry verticals served
   - Required certifications
   - List of consultant emails registered
   - Available capacity (hours per week)
   - Geographic location preferences

2. **Consultants** - Uses email as identifier:
   - Name
   - Practice area
   - Skill level
   - Certifications
   - Availability

All data is currently stored in memory for this learning exercise. In a production environment, this would be backed by a robust database system.

## Future Enhancements

This exercise will guide you through implementing:
- Capability maturity assessments
- Intelligent team matching algorithms  
- Analytics dashboards for practice leads
- Integration with project management systems
- Advanced search and filtering capabilities
