from fastapi import APIRouter
from routes.users import router as users_router
from routes.chats import router as chats_router
from routes.messages import router as messages_router
from routes.medicines import router as medicines_router
from routes.medications import router as medications_router
from routes.medication_schedules import router as medication_schedules_router
from routes.bp_schedules import router as bp_schedules_router
from routes.sugar_schedules import router as sugar_schedules_router
from routes.medication_logs import router as medication_logs_router
from routes.bp_logs import router as bp_logs_router
from routes.sugar_logs import router as sugar_logs_router
from routes.insights import router as insights_router
from routes.alerts import router as alerts_router
from routes.reports import router as reports_router

router = APIRouter()

# Include all routers
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(chats_router, prefix="/chats", tags=["Chats"])
router.include_router(messages_router, prefix="/messages", tags=["Messages"])
router.include_router(medicines_router, prefix="/medicines", tags=["Medicines"])
router.include_router(medications_router, prefix="/medications", tags=["Medications"])
router.include_router(medication_schedules_router, prefix="/medication_schedules", tags=["Medication_Schedules"])
router.include_router(bp_schedules_router, prefix="/bp_schedules", tags=["BP_Schedules"])
router.include_router(sugar_schedules_router, prefix="/sugar_schedules", tags=["Sugar_Schedules"])
router.include_router(medication_logs_router, prefix="/medication_logs", tags=["Medication_Logs"])
router.include_router(bp_logs_router, prefix="/bp_logs", tags=["BP_Logs"])
router.include_router(sugar_logs_router, prefix="/sugar_logs", tags=["Sugar_Logs"])
router.include_router(insights_router, prefix="/insights", tags=["Insights"])
router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
router.include_router(reports_router, prefix="/reports", tags=["Reports"])