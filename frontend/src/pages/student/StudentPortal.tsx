/**
 * PEVN Frontend — Student Portal Master Workspace (Phase 14B)
 *
 * Primary container for the authenticated student self-service experience:
 * - Subtabs: Inicio | Mis Asignaturas | Mis Tareas | Mis Calificaciones | Mi Asistencia | Clases Virtuales | Mi Perfil
 * - URL Synchronization with `?tab=...` and modal deep links
 * - Security-First: Identity derived server-side from JWT claims
 * - Complete Error, Loading, and Empty states
 */

import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { studentApi } from '@/services/student'
import type {
  StudentActivityItemResponse,
  StudentDashboardResponse,
  StudentGradeItemResponse,
  StudentSubjectItemResponse,
  StudentTab,
  StudentVirtualClassroomItemResponse,
} from '@/types/student'
import { StudentHeader } from '@/components/student/StudentHeader'
import { StudentNavbar } from '@/components/student/StudentNavbar'
import { StudentLoadingSkeleton } from '@/components/student/StudentLoadingSkeleton'
import { StudentTaskDetailModal } from '@/components/student/StudentTaskDetailModal'
import { StudentVirtualClassModal } from '@/components/student/StudentVirtualClassModal'
import { StudentDashboardView } from './StudentDashboardView'
import { StudentSubjectsView } from './StudentSubjectsView'
import { StudentTasksView } from './StudentTasksView'
import { StudentGradesView } from './StudentGradesView'
import { StudentAttendanceView } from './StudentAttendanceView'
import { StudentVirtualClassesView } from './StudentVirtualClassesView'
import { StudentCommunicationsView } from './StudentCommunicationsView'
import { StudentNewsView } from './StudentNewsView'
import { StudentIncidentsView } from './StudentIncidentsView'
import { StudentProfileView } from './StudentProfileView'

export const StudentPortal: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as StudentTab) || 'dashboard'
  const [activeTab, setActiveTab] = useState<StudentTab>(initialTab)

  // Master data states
  const [dashboardData, setDashboardData] = useState<StudentDashboardResponse | null>(null)
  const [subjects, setSubjects] = useState<StudentSubjectItemResponse[]>([])
  const [allActivities, setAllActivities] = useState<StudentActivityItemResponse[]>([])
  const [allGrades, setAllGrades] = useState<StudentGradeItemResponse[]>([])
  const [attendanceData, setAttendanceData] = useState<any | null>(null)
  const [virtualClassrooms, setVirtualClassrooms] = useState<StudentVirtualClassroomItemResponse[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modals & Selected items
  const [selectedTask, setSelectedTask] = useState<StudentActivityItemResponse | null>(null)
  const [selectedVirtualClass, setSelectedVirtualClass] = useState<StudentVirtualClassroomItemResponse | null>(null)
  const [virtualClassModalMode, setVirtualClassModalMode] = useState<'join' | 'recordings'>('join')
  const [selectedSubjectFilter, setSelectedSubjectFilter] = useState<string | null>(null)

  // Sync tab with URL search parameter
  useEffect(() => {
    const tabParam = searchParams.get('tab') as StudentTab
    if (
      tabParam &&
      [
        'dashboard',
        'subjects',
        'tasks',
        'grades',
        'attendance',
        'virtual-classes',
        'communications',
        'news',
        'incidents',
        'profile',
      ].includes(tabParam)
    ) {
      setActiveTab(tabParam)
    }
  }, [searchParams])

  const handleTabChange = (newTab: StudentTab) => {
    setActiveTab(newTab)
    setSearchParams({ tab: newTab })
  }

  // Load all student portal data concurrently
  const loadStudentData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dash, subjList, actList, gradeList, attList, vcList] = await Promise.all([
        studentApi.getDashboard(),
        studentApi.listSubjects(),
        studentApi.listActivities(),
        studentApi.listGrades(),
        studentApi.listAttendance(),
        studentApi.listVirtualClassrooms(),
      ])

      setDashboardData(dash)
      setSubjects(subjList.items)
      setAllActivities(actList.items)
      setAllGrades(gradeList.items)
      setAttendanceData(attList)
      setVirtualClassrooms(vcList.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar los datos del portal estudiantil.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadStudentData()
  }, [])

  // Navigation callbacks
  const handleSelectSubjectForTasks = (subjectId: string) => {
    setSelectedSubjectFilter(subjectId)
    handleTabChange('tasks')
  }

  const handleOpenJoinClass = (classroom: StudentVirtualClassroomItemResponse) => {
    setSelectedVirtualClass(classroom)
    setVirtualClassModalMode('join')
  }

  const handleOpenRecordings = (classroom: StudentVirtualClassroomItemResponse) => {
    setSelectedVirtualClass(classroom)
    setVirtualClassModalMode('recordings')
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '1.5rem', minHeight: '80vh' }}>
      {/* 1. Header Profile Banner */}
      <StudentHeader
        profile={dashboardData?.profile || null}
        onRefresh={loadStudentData}
        loading={loading}
      />

      {/* 2. Sub-navigation tabs */}
      <StudentNavbar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        pendingTasksCount={dashboardData?.pending_activities_count || 0}
        upcomingClassesCount={
          virtualClassrooms.filter((c) => c.status === 'RUNNING' || c.status === 'SCHEDULED').length
        }
      />

      {/* 3. Error Banner */}
      {error && (
        <div
          style={{
            backgroundColor: '#FEE2E2',
            border: '1px solid #FCA5A5',
            color: '#991B1B',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.25rem' }}>⚠️</span>
            <span>{error}</span>
          </div>

          <button
            onClick={loadStudentData}
            style={{
              backgroundColor: '#DC2626',
              color: '#FFFFFF',
              border: 'none',
              padding: '0.4rem 0.85rem',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Reintentar
          </button>
        </div>
      )}

      {/* 4. Active Tab Content with Loading Skeletons */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <StudentLoadingSkeleton type="metrics" count={4} />
          <StudentLoadingSkeleton type="cards" count={4} />
        </div>
      ) : (
        <>
          {activeTab === 'dashboard' && dashboardData && (
            <StudentDashboardView
              data={dashboardData}
              onNavigateTab={handleTabChange}
              onViewTaskDetails={(act) => setSelectedTask(act)}
              onJoinClass={handleOpenJoinClass}
              onViewRecordings={handleOpenRecordings}
            />
          )}

          {activeTab === 'subjects' && (
            <StudentSubjectsView
              subjects={subjects}
              onSelectSubjectForTasks={handleSelectSubjectForTasks}
            />
          )}

          {activeTab === 'tasks' && (
            <StudentTasksView
              activities={allActivities}
              subjects={subjects}
              selectedSubjectId={selectedSubjectFilter}
              onViewTaskDetails={(act) => setSelectedTask(act)}
            />
          )}

          {activeTab === 'grades' && (
            <StudentGradesView
              grades={allGrades}
              averageScore={dashboardData?.attendance_summary ? (dashboardData as any).average_score : null}
              subjects={subjects}
            />
          )}

          {activeTab === 'attendance' && attendanceData && (
            <StudentAttendanceView
              attendanceItems={attendanceData.items}
              summary={attendanceData.summary}
            />
          )}

          {activeTab === 'virtual-classes' && (
            <StudentVirtualClassesView
              classrooms={virtualClassrooms}
              onJoinClass={handleOpenJoinClass}
              onViewRecordings={handleOpenRecordings}
            />
          )}

          {activeTab === 'communications' && (
            <StudentCommunicationsView
              onBackToDashboard={() => handleTabChange('dashboard')}
            />
          )}

          {activeTab === 'news' && (
            <StudentNewsView
              onBackToDashboard={() => handleTabChange('dashboard')}
            />
          )}

          {activeTab === 'incidents' && (
            <StudentIncidentsView
              onBackToDashboard={() => handleTabChange('dashboard')}
            />
          )}

          {activeTab === 'profile' && dashboardData && (
            <StudentProfileView profile={dashboardData.profile} />
          )}
        </>
      )}

      {/* 5. Modals */}
      {selectedTask && (
        <StudentTaskDetailModal
          activity={selectedTask}
          onClose={() => setSelectedTask(null)}
          onSubmitted={() => {
            void loadStudentData()
          }}
        />
      )}

      {selectedVirtualClass && (
        <StudentVirtualClassModal
          classroom={selectedVirtualClass}
          mode={virtualClassModalMode}
          onClose={() => setSelectedVirtualClass(null)}
        />
      )}
    </div>
  )
}

export default StudentPortal
