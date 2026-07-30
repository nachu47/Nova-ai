import{render,screen}from'@testing-library/react';import{MemoryRouter}from'react-router-dom';import{expect,test,vi}from'vitest';import{LoginPage}from'@/pages/LoginPage'
vi.mock('@/contexts/AuthContext',()=>({useAuth:()=>({user:null,login:vi.fn(),loading:false})}))
test('renders the Nova sign-in form',()=>{render(<MemoryRouter><LoginPage/></MemoryRouter>);expect(screen.getByRole('heading',{name:/welcome to nova/i})).toBeInTheDocument();expect(screen.getByRole('button',{name:/sign in/i})).toBeInTheDocument()})
