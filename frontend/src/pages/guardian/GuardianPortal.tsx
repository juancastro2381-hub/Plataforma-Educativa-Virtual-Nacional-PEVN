/**
 * PEVN Frontend — Guardian Portal Master Coordinator (Phase 14C)
 *
 * Coordinates state, active child context, URL synchronization (?tab=...&student_id=...),
 * Anti-IDOR authorization validation, and renders guardian subviews.
 *
 * Security:
 * - Anti-IDOR: Selected student ID must be strictly present in GET /guardian/students.
 * - Stale Data Prevention: Clears child state immediately upon student switch.
 * - Read-Only Supervision: Guardian acts exclusively as observer/supervisor.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { guardianApi } from '@/services/guardian'
import type {
  GuardianChildActivitiesListResponse,
  GuardianChildAttendanceListResponse,
  GuardianChildGradesListResponse,
  GuardianChildItemResponse,
  GuardianChildOverviewResponse,
  GuardianChildVirtualClassroomsListResponse,
  GuardianProfileResponse,
  GuardianTab,
} from '@/types/guardian'
import type { StudentActivityItemResponse } from '@/types/student'
import { GuardianHeader } from '@/components/guardian/GuardianHeader'
import { GuardianNavbar } from '@/components/guardian/GuardianNavbar'
import { GuardianStudentSwitcher } from '@/components/guardian/GuardianStudentSwitcher'
import { GuardianEmptyState } from '@/components/guardian/GuardianEmptyState'
import { GuardianTaskDetailModal } from '@/components/guardian/GuardianTaskDetailModal'

import { GuardianDashboardView } from './GuardianDashboardView'
import { GuardianStudentsView } from './GuardianStudentsView'
import { GuardianAcademicView } from './GuardianAcademicView'
import { GuardianTasksView } from './GuardianTasksView'
import { GuardianGradesView } from './GuardianGradesView'
import { GuardianAttendanceView } from './GuardianAttendanceView'
import { GuardianVirtualClassesView } from './GuardianVirtualClassesView'
import { GuardianCommunicationsView } from './GuardianCommunicationsView'
import { GuardianNewsView } from './GuardianNewsView'
import { GuardianIncidentsView } from './GuardianIncidentsView'
import { GuardianProfileView } from './GuardianProfileView'

const VALID_TABS: GuardianTab[] = [
  'dashboard',
  'students',
  'academic',
  'tasks',
  'grades',
  'attendance',
  'virtual-classes',
  'communications',
  'news',
  'incidents',
  'profile',
]

export const GuardianPortal: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()

  const tabParam = searchParams.get('tab') as GuardianTab
  const activeTab: GuardianTab = tabParam && VALID_TABS.includes(tabParam) ? tabParam : 'dashboard'

  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(
    () => searchParams.get('student_id')
  )

  // Global Guardian State
  const [profile, setProfile] = useState<GuardianProfileResponse | null>(null)
  const [students, setStudents] = useState<GuardianChildItemResponse[]>([])
  const [initialLoading, setInitialLoading] = useState(true)
  const [globalError, setGlobalError] = useState<string | null>(null)

  // Child-Specific Data State (Strictly cleared on student switch)
  const [childLoading, setChildLoading] = useState(false)
  const [overview, setOverview] = useState<GuardianChildOverviewResponse | null>(null)
  const [activities, setActivities] = useState<GuardianChildActivitiesListResponse | null>(null)
  const [grades, setGrades] = useState<GuardianChildGradesListResponse | null>(null)
  const [attendance, setAttendance] = useState<GuardianChildAttendanceListResponse | null>(null)
  const [virtualClasses, setVirtualClasses] = useState<GuardianChildVirtualClassroomsListResponse | null>(null)
  const [selectedTaskModal, setSelectedTaskModal] = useState<StudentActivityItemResponse | null>(null)

  // Handle Tab Switch
  const handleTabChange = (newTab: GuardianTab) => {
    const next: Record<string, string> = { tab: newTab }
    if (selectedStudentId) {
      next.student_id = selectedStudentId
    }
    setSearchParams(next)
  }

  // 1. Initial Load: Fetch Profile and Authorized Students List
  const loadInitialData = async () => {
    setInitialLoading(true)
    setGlobalError(null)

    try {
      const [profileRes, studentsRes] = await Promise.all([
        guardianApi.getProfile(),
        guardianApi.listStudents(),
      ])

      setProfile(profileRes)
      const fetchedStudents = studentsRes.items || []
      setStudents(fetchedStudents)

      // Anti-IDOR validation: ensure initial selectedStudentId belongs to authorized children
      if (fetchedStudents.length > 0) {
        const urlStudentId = searchParams.get('student_id')
        const urlMatch = fetchedStudents.find((s) => s.student_id === urlStudentId)
        const activeId = urlMatch ? urlMatch.student_id : fetchedStudents[0].student_id
        setSelectedStudentId(activeId)
      } else {
        setSelectedStudentId(null)
      }
    } catch (err: any) {
      console.error('Error fetching guardian portal initial data:', err)
      setGlobalError('No fue posible cargar la información institucional del acudiente.')
    } finally {
      setInitialLoading(false)
    }
  }

  useEffect(() => {
    void loadInitialData()
  }, [])

  // 2. Fetch Child Data when selectedStudentId changes
  const loadChildData = useCallback(async (studentId: string) => {
    // Stale Data Prevention: Reset all child data immediately
    setOverview(null)
    setActivities(null)
    setGrades(null)
    setAttendance(null)
    setVirtualClasses(null)
    setChildLoading(true)

    try {
      const [overviewRes, activitiesRes, gradesRes, attendanceRes, virtualClassesRes] =
        await Promise.all([
          guardianApi.getChildOverview(studentId),
          guardianApi.listChildActivities(studentId),
          guardianApi.listChildGrades(studentId),
          guardianApi.listChildAttendance(studentId),
          guardianApi.listChildVirtualClassrooms(studentId),
        ])

      setOverview(overviewRes)
      setActivities(activitiesRes)
      setGrades(gradesRes)
      setAttendance(attendanceRes)
      setVirtualClasses(virtualClassesRes)
    } catch (err: any) {
      console.error(`Error fetching data for student ${studentId}:`, err)
      // Anti-IDOR safe fallback
      setOverview(null)
    } finally {
      setChildLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedStudentId) {
      // Validate that selectedStudentId is authorized
      const isAuthorized = students.some((s) => s.student_id === selectedStudentId)
      if (isAuthorized) {
        loadChildData(selectedStudentId)
      }
    }
  }, [selectedStudentId, students, loadChildData])

  // Handle Student Selection Switch
  const handleSelectStudent = (studentId: string) => {
    // Validate anti-IDOR client-side before setting state
    const match = students.find((s) => s.student_id === studentId)
    if (!match) return

    setSelectedStudentId(studentId)
    const next: Record<string, string> = { tab: activeTab, student_id: studentId }
    setSearchParams(next)
    void loadChildData(studentId)
  }

  // Active Child Helper
  const activeChild = students.find((s) => s.student_id === selectedStudentId)

  // Render Subview Content
  const renderContent = () => {
    if (globalError) {
      return (
        <GuardianEmptyState
          icon="⚠️"
          title="Error de Acceso"
          description={globalError}
          actionLabel="Reintentar"
          onAction={loadInitialData}
        />
      )
    }

    if (!initialLoading && students.length === 0 && activeTab !== 'profile') {
      return (
        <GuardianEmptyState
          icon="👨‍👧‍👦"
          title="Sin estudiantes vinculados"
          description="No se encuentran estudiantes asignados bajo su tutoría legal en el sistema institucional. Por favor comuníquese con la administración escolar."
          actionLabel="Ver Mi Perfil"
          onAction={() => handleTabChange('profile')}
        />
      )
    }

    switch (activeTab) {
      case 'dashboard':
        return (
          <GuardianDashboardView
            overview={overview}
            loading={childLoading || initialLoading}
            onTabChange={handleTabChange}
            onSelectTask={setSelectedTaskModal}
          />
        )

      case 'students':
        return (
          <GuardianStudentsView
            students={students}
            selectedStudentId={selectedStudentId}
            onSelectStudent={(id) => {
              handleSelectStudent(id)
              handleTabChange('dashboard')
            }}
            loading={initialLoading}
          />
        )

      case 'academic':
        return (
          <GuardianAcademicView
            gradesData={grades}
            loading={childLoading}
            childName={activeChild?.full_name}
          />
        )

      case 'tasks':
        return (
          <GuardianTasksView
            activitiesData={activities}
            loading={childLoading}
            childName={activeChild?.full_name}
          />
        )

      case 'grades':
        return (
          <GuardianGradesView
            gradesData={grades}
            loading={childLoading}
            childName={activeChild?.full_name}
            studentId={activeChild?.student_id}
          />
        )

      case 'attendance':
        return (
          <GuardianAttendanceView
            attendanceData={attendance}
            loading={childLoading}
            childName={activeChild?.full_name}
          />
        )

      case 'virtual-classes':
        return (
          <GuardianVirtualClassesView
            classroomsData={virtualClasses}
            loading={childLoading}
            childName={activeChild?.full_name}
          />
        )

      case 'communications':
        return (
          <GuardianCommunicationsView
            onBackToDashboard={() => handleTabChange('dashboard')}
          />
        )

      case 'news':
        return (
          <GuardianNewsView
            onBackToDashboard={() => handleTabChange('dashboard')}
          />
        )

      case 'incidents':
        return (
          <GuardianIncidentsView
            selectedStudentId={selectedStudentId}
            selectedStudentName={activeChild?.full_name}
            onBackToDashboard={() => handleTabChange('dashboard')}
          />
        )

      case 'profile':
        return (
          <GuardianProfileView
            profile={profile}
            loading={initialLoading}
          />
        )

      default:
        return (
          <GuardianDashboardView
            overview={overview}
            loading={childLoading}
            onTabChange={handleTabChange}
            onSelectTask={setSelectedTaskModal}
          />
        )
    }
  }

  return (
    <div
      style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '1.5rem 1rem',
        minHeight: '80vh',
      }}
    >
      {/* 1. Header with Guardian Identity */}
      <GuardianHeader
        profile={profile}
        loading={initialLoading || childLoading}
        onRefresh={() => {
          void loadInitialData()
          if (selectedStudentId) void loadChildData(selectedStudentId)
        }}
      />

      {/* 2. Multi-Student Context Switcher */}
      {students.length > 0 && activeTab !== 'students' && activeTab !== 'profile' && (
        <GuardianStudentSwitcher
          students={students}
          selectedStudentId={selectedStudentId}
          onSelectStudent={handleSelectStudent}
          loading={childLoading}
        />
      )}

      {/* 3. 11 Navigation Tabs */}
      <GuardianNavbar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        pendingTasksCount={overview?.pending_tasks_count || 0}
        upcomingClassesCount={overview?.upcoming_virtual_classrooms?.length || 0}
      />

      {/* 4. Active Subview Content */}
      <main id="guardian-content-area">{renderContent()}</main>

      {/* 5. Global Read-Only Task Modal */}
      {selectedTaskModal && (
        <GuardianTaskDetailModal
          activity={selectedTaskModal}
          onClose={() => setSelectedTaskModal(null)}
        />
      )}
    </div>
  )
}
