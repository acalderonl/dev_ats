import { Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginView } from '@/views/LoginView'
import { DashboardView } from '@/views/DashboardView'
import { CargosView } from '@/views/CargosView'
import { VacantesView } from '@/views/VacantesView'
import { PipelineView } from '@/views/PipelineView'
import { ContactosView } from '@/views/ContactosView'
import { EvaluacionesView } from '@/views/EvaluacionesView'
import { UsuariosView } from '@/views/UsuariosView'
import { ConfiguracionView } from '@/views/ConfiguracionView'
import { PostularView } from '@/views/public/PostularView'
import { VacanteExpiradaView } from '@/views/public/VacanteExpiradaView'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginView />} />
      <Route path="/postular/:slug" element={<PostularView />} />
      <Route path="/vacante-expirada" element={<VacanteExpiradaView />} />

      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardView />} />
        <Route path="/cargos" element={<CargosView />} />
        <Route path="/vacantes" element={<VacantesView />} />
        <Route path="/pipeline" element={<PipelineView />} />
        <Route path="/contactos" element={<ContactosView />} />
        <Route path="/evaluaciones" element={<EvaluacionesView />} />
        <Route path="/usuarios" element={<UsuariosView />} />
        <Route path="/configuracion" element={<ConfiguracionView />} />
      </Route>
    </Routes>
  )
}
