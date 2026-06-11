# Spoken Social — Development Guide (CLAUDE.md)

This file contains local development commands, project style rules, and specific design instructions that guide coding agents (like Claude and Gemini) to maintain high-quality code and professional frontend design aesthetics in this repository.

## 🛠 Command Reference

### Frontend Commands (React/Vite)
- **Install dependencies:** `npm install` (within `frontend/`)
- **Run dev server:** `npm run dev`
- **Build production bundle:** `npm run build`
- **Lint code:** `npm run lint`

### Backend Commands (FastAPI)
- **Install dependencies:** `pip install -r requirements.txt` (within `backend/`)
- **Run dev server:** `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **Run migrations:** `alembic upgrade head`
- **Create new migration:** `alembic revision --autogenerate -m "description"`
- **Run tests:** `pytest` (within `backend/`)

---

## 🎨 Premium Frontend Design Guidelines

To avoid generic "AI-templated" designs, all frontend components must strictly adhere to the following design system rules:

### 1. Unified Theme & Design Tokens
Always use custom design variables configured in `frontend/src/index.css` rather than ad-hoc Tailwind values or raw hex codes.
- **Brand Colors:** Use `--color-primary` (Deep Indigo), `--color-secondary` (Teal), and semantic highlights (`--color-success`, `--color-warning`, `--color-danger`, `--color-xp-gold`).
- **Typography:** Use `--font-sans` (`Inter` font family) for body text and navigation, and `--font-mono` (`Space Grotesk`) for XP numbers, scores, and headings.
- **Surfaces:** Use Tailwind classes corresponding to theme surfaces: `bg-background` for application body, `bg-card` for cards, and border classes matching `--color-border`.

### 2. Avoiding "AI Slop" & Generic Layouts
- **No Generic Blue-Purple Gradients:** Unless explicitly requested, do not use basic gradients (`bg-gradient-to-r from-blue-500 to-purple-500`). Use solid custom colors or complex, layered gradients matching the Indigo-Teal brand guidelines.
- **Opinionated Spacing:** Use distinct padding/margins and strong borders (`border-border`) to give interfaces a structured, professional appearance.
- **No Simple Cards:** Standard cards should have subtle hover scales (`hover:scale-[1.01]`), smooth transition properties (`transition-all duration-300`), and premium border transitions.

### 3. Native Dark Mode Support
The application is dark-mode-first. Always write classes that handle both modes gracefully:
- Utilize Tailwind's custom dark variant `dark:` (e.g., `dark:bg-card`, `dark:text-foreground`).
- Test styling transitions under both light and dark modes.

### 4. Interactive Micro-Animations
Make interfaces feel alive with transitions and micro-animations defined in `index.css`:
- **Celebration / XP Gains:** Trigger animations like `confetti-fall`, `celebration-icon-pop`, or `glow-pulse` when a student earns XP or completes a task.
- **Loading:** Use `shimmer` skeleton loaders instead of plain loading text or spinners.
- **Transitions:** Every interactive state (hover, focus, active) must have a subtle ease transition (`transition duration-200 ease-in-out`).

### 5. Mobile-First Layouts
Most students access the platform on mobile.
- Implement responsive breakpoints (`sm`, `md`, `lg`) carefully.
- Keep primary navigation items in mobile bottom bars and ensure touch targets are at least `44px x 44px`.

---

## 💻 Code Style Conventions

### React & TypeScript
- Use functional components with arrow syntax and explicit return types (`React.FC` or return type annotation).
- Use TypeScript for strict typing of components, props, hooks, and stores. Avoid using `any`.
- Keep components small, focused, and reusable. Organize them logically under `components/`.
- Manage global UI and application state using **Zustand** stores (`frontend/src/store/`).

### Python & FastAPI
- Write async route handlers in `routes/` and annotate all parameter/return types using Pydantic schemas.
- Ensure proper dependency injection (`Depends(get_db)`, `Depends(get_current_user)`).
- Manage database sessions strictly with context managers or FastAPI dependencies to prevent connection leaks.
